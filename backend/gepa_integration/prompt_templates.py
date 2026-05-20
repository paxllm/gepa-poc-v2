"""
Prompt templates for resume evaluation within the GEPA system.
These are the system prompts used when a candidate's prompts are applied to evaluate a resume.
"""


RESUME_EVALUATION_SYSTEM = """You are an expert hiring evaluator. You will be given:
1. A job description
2. Company core values with descriptions
3. An evaluation prompt (the "Talent Lens")
4. A candidate's resume

Your task is to evaluate the candidate's resume according to the Talent Lens prompt.

You MUST respond with valid JSON in this exact format:
{
    "score": <number from 1 to 5>,
    "rationale": "<detailed explanation of your scoring>"
}

Scoring guide:
- 1: No evidence of the evaluated criteria
- 2: Minimal evidence, significant gaps
- 3: Moderate evidence, meets basic expectations
- 4: Strong evidence, exceeds expectations
- 5: Exceptional evidence, outstanding match

Be objective, evidence-based, and specific in your rationale.
"""

SEED_GENERATION_SYSTEM = """You are an expert hiring prompt engineer. Your task is to write evaluation prompts ("Talent Lenses") used to score software engineering resumes.

Each lens must:
- Focus on ONE evaluation angle (preserving the user's intent for that slot)
- Be tailored to the specific job description and company core values provided
- Include a clear 1–5 scoring rubric with level descriptions
- Instruct the evaluator to return ONLY valid JSON: {"score": <integer 1-5>, "rationale": "<2-3 sentences>"}
- NOT include the job description or core values in the lens text (those are injected separately at evaluation time)

Output exactly 5 distinct lenses as a JSON object with keys prompt_1 through prompt_5.
Return ONLY the JSON object, no markdown fences or extra text.
"""


def format_core_values(core_values: list[dict[str, str]]) -> str:
    """Format core values as markdown bullet list."""
    return "\n".join(
        f"- **{cv['name']}**: {cv['description']}"
        for cv in core_values
    )


EVALUATION_FOCUS_MARKER = "## Evaluation Focus (Talent Lens)"
COMPOSED_PROMPT_FOOTER = "\n\nEvaluate the candidate against"


def is_composed_prompt(text: str) -> bool:
    """True if text is a legacy full prompt with embedded job description."""
    return text.strip().startswith("## Job Description")


def extract_user_lens(text: str) -> str:
    """Return lens-only text, stripping legacy composed prompt wrappers if present."""
    stripped = text.strip()
    if not is_composed_prompt(stripped):
        return stripped

    idx = stripped.find(EVALUATION_FOCUS_MARKER)
    if idx == -1:
        return stripped

    lens = stripped[idx + len(EVALUATION_FOCUS_MARKER) :].lstrip("\n")
    footer_idx = lens.find(COMPOSED_PROMPT_FOOTER)
    if footer_idx != -1:
        lens = lens[:footer_idx]
    return lens.strip()


def normalize_prompts(prompts: list[str]) -> list[str]:
    """Normalize a list of user prompts to lens-only text."""
    return [extract_user_lens(p).strip() for p in prompts]


def compose_talent_lens_prompt(
    user_lens: str,
    job_description: str,
    core_values: list[dict[str, str]],
) -> str:
    """Build the full evaluation instruction from a lens plus shared job context."""
    core_values_text = format_core_values(core_values)
    lens = extract_user_lens(user_lens)

    return f"""## Job Description
{job_description.strip()}

## Company Core Values
{core_values_text}

## Evaluation Focus (Talent Lens)
{lens}

Evaluate the candidate against the job description and all core values above,
using the evaluation focus as your primary scoring lens.
"""


def build_seed_candidate(
    prompts: list[str],
    job_description: str,
    core_values: list[dict[str, str]],
) -> dict[str, str]:
    """Build a GEPA seed candidate from user-authored lens text (no JD/CV duplication)."""
    if len(prompts) != 5:
        raise ValueError(f"Expected exactly 5 prompts, got {len(prompts)}")
    if not job_description.strip():
        raise ValueError("Job description is required to build the seed candidate")
    if not core_values:
        raise ValueError("Core values are required to build the seed candidate")

    normalized = normalize_prompts(prompts)
    return {f"prompt_{i + 1}": lens for i, lens in enumerate(normalized)}


def build_seed_generation_messages(
    user_prompts: list[str],
    job_description: str,
    core_values: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Build messages for LLM seed candidate generation."""
    if len(user_prompts) != 5:
        raise ValueError(f"Expected exactly 5 user prompts, got {len(user_prompts)}")

    core_values_text = format_core_values(core_values)
    angles = "\n\n".join(
        f"### User angle {i + 1}\n{user_prompts[i].strip()}"
        for i in range(5)
    )

    user_content = f"""## Job Description
{job_description.strip()}

## Company Core Values
{core_values_text}

## User-Provided Evaluation Angles
{angles}

For each user angle (1–5), write a complete evaluation lens that preserves that angle's focus but tailors criteria to this role and core values. Each lens must include a 1–5 rubric and JSON output instructions.

Return ONLY valid JSON in this exact shape:
{{"prompt_1": "<lens 1>", "prompt_2": "<lens 2>", "prompt_3": "<lens 3>", "prompt_4": "<lens 4>", "prompt_5": "<lens 5>"}}
"""

    return [
        {"role": "system", "content": SEED_GENERATION_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_evaluation_prompt(
    talent_lens_prompt: str,
    resume_text: str,
) -> list[dict[str, str]]:
    """
    Build the full messages array for evaluating a resume with a talent lens prompt.

    Args:
        talent_lens_prompt: Full evaluation prompt (job description, core values,
            and lens already composed for seed/evolved candidates).
        resume_text: The parsed resume text.

    Returns:
        Messages list for LLM chat completion.
    """
    user_content = f"""{talent_lens_prompt.strip()}

## Candidate Resume
{resume_text}

Please evaluate this candidate according to the instructions above.
Respond with JSON: {{"score": <1-5>, "rationale": "<detailed reasoning>"}}
"""

    return [
        {"role": "system", "content": RESUME_EVALUATION_SYSTEM},
        {"role": "user", "content": user_content},
    ]
