"""
GEPA adapter for multi-prompt resume hiring evaluation.

Runs all 5 talent-lens prompts per resume, aggregates scores, and scores
each example as 1.0 (correct hire/reject prediction) or 0.0 (mismatch).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, TypedDict

from backend.core.config import get_settings
from backend.core.litellm_client import completion_with_retry
from backend.gepa_integration.evaluator import _parse_prompt_score
from backend.gepa_integration.prompt_templates import (
    build_evaluation_prompt,
    compose_talent_lens_prompt,
    extract_user_lens,
)
from gepa.core.adapter import EvaluationBatch, GEPAAdapter

PROMPT_KEYS = ("prompt_1", "prompt_2", "prompt_3", "prompt_4", "prompt_5")
LLM_TIMEOUT_SECONDS = 120


class HiringDataInst(TypedDict):
    input: str
    additional_context: dict[str, str]
    answer: str


class PromptRunResult(TypedDict):
    score: float
    rationale: str
    response_text: str


class HiringTrajectory(TypedDict):
    data: HiringDataInst
    prompt_results: dict[str, PromptRunResult]
    aggregate_score: float
    prediction: str
    expected_label: str
    is_correct: bool
    feedback_by_prompt: dict[str, str]


class HiringRolloutOutput(TypedDict):
    aggregate_score: float
    prediction: str
    prompt_scores: dict[str, float]


HiringReflectiveRecord = TypedDict(
    "HiringReflectiveRecord",
    {
        "Inputs": str,
        "Generated Outputs": str,
        "Feedback": str,
    },
)


def _build_prompt_feedback(
    *,
    prompt_key: str,
    prompt_score: float,
    rationale: str,
    aggregate_score: float,
    prediction: str,
    expected_label: str,
    hire_threshold: float,
    resume_snippet: str,
) -> str:
    prompt_prediction = "Hired" if prompt_score >= hire_threshold else "Rejected"
    is_correct = prediction == expected_label

    lines = [
        f"Prompt ({prompt_key}) score: {prompt_score}/5",
        f"Prompt-only prediction (threshold={hire_threshold}): {prompt_prediction}",
        f"Aggregate score (all 5 prompts): {aggregate_score:.2f}/5",
        f"Final prediction: {prediction}",
        f"Expected label: {expected_label}",
        f"Overall correct: {'Yes' if is_correct else 'NO - MISMATCH'}",
        f"Rationale: {rationale}",
    ]

    if not is_correct:
        if prediction == "Hired" and expected_label == "Rejected":
            lines.append(
                "ISSUE: The prompt set scored this candidate too HIGH. "
                "This prompt may be too lenient or missing rejection criteria."
            )
        else:
            lines.append(
                "ISSUE: The prompt set scored this candidate too LOW. "
                "This prompt may be too strict or not recognizing relevant qualifications."
            )
        lines.append(f"Resume snippet: {resume_snippet}")

    return "\n".join(lines)


def _evaluate_one_prompt(
    key: str,
    candidate: dict[str, str],
    resume_text: str,
    *,
    task_lm_model: str,
    hire_threshold: float,
    job_description: str,
    core_values: list[dict[str, str]],
) -> tuple[str, PromptRunResult]:
    """Evaluate a single prompt component against one resume."""
    lens = extract_user_lens(candidate[key])
    composed = compose_talent_lens_prompt(lens, job_description, core_values)
    messages = build_evaluation_prompt(
        talent_lens_prompt=composed,
        resume_text=resume_text,
    )
    completion = completion_with_retry(
        model=task_lm_model,
        messages=messages,
        timeout=LLM_TIMEOUT_SECONDS,
    )
    response_text = completion.choices[0].message.content or ""
    score = _parse_prompt_score(response_text, hire_threshold)

    try:
        parsed = json.loads(response_text)
        rationale = str(parsed.get("rationale", "No rationale provided"))
    except (json.JSONDecodeError, ValueError, TypeError):
        rationale = response_text[:500]

    return key, {
        "score": score,
        "rationale": rationale,
        "response_text": response_text,
    }


def _evaluate_single_resume(
    data: HiringDataInst,
    candidate: dict[str, str],
    *,
    task_lm_model: str,
    hire_threshold: float,
    job_description: str,
    core_values: list[dict[str, str]],
) -> tuple[float, HiringRolloutOutput, HiringTrajectory | None]:
    """Score one resume against a 5-prompt candidate (prompts evaluated with limited parallelism)."""
    resume_text = data["input"]
    expected_label = data["answer"]
    max_workers = max(1, get_settings().llm_max_parallel)

    prompt_results: dict[str, PromptRunResult] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _evaluate_one_prompt,
                key,
                candidate,
                resume_text,
                task_lm_model=task_lm_model,
                hire_threshold=hire_threshold,
                job_description=job_description,
                core_values=core_values,
            ): key
            for key in PROMPT_KEYS
        }
        for future in as_completed(futures):
            key, result = future.result()
            prompt_results[key] = result

    prompt_scores = {key: prompt_results[key]["score"] for key in PROMPT_KEYS}
    numeric_scores = list(prompt_scores.values())

    aggregate_score = sum(numeric_scores) / len(numeric_scores)
    prediction = "Hired" if aggregate_score >= hire_threshold else "Rejected"
    is_correct = prediction == expected_label
    gepa_score = 1.0 if is_correct else 0.0

    resume_snippet = resume_text[:500]
    feedback_by_prompt = {
        key: _build_prompt_feedback(
            prompt_key=key,
            prompt_score=prompt_results[key]["score"],
            rationale=prompt_results[key]["rationale"],
            aggregate_score=aggregate_score,
            prediction=prediction,
            expected_label=expected_label,
            hire_threshold=hire_threshold,
            resume_snippet=resume_snippet,
        )
        for key in PROMPT_KEYS
    }

    output: HiringRolloutOutput = {
        "aggregate_score": aggregate_score,
        "prediction": prediction,
        "prompt_scores": prompt_scores,
    }

    trajectory: HiringTrajectory = {
        "data": data,
        "prompt_results": prompt_results,
        "aggregate_score": aggregate_score,
        "prediction": prediction,
        "expected_label": expected_label,
        "is_correct": is_correct,
        "feedback_by_prompt": feedback_by_prompt,
    }

    return gepa_score, output, trajectory


class HiringAdapter(GEPAAdapter[HiringDataInst, HiringTrajectory, HiringRolloutOutput]):
    """Evaluate 5-prompt candidates on resume batches for GEPA optimization."""

    def __init__(
        self,
        task_lm_model: str,
        hire_threshold: float | None = None,
        job_id: int | None = None,
        run_status: dict[int, dict[str, Any]] | None = None,
        job_description: str = "",
        core_values: list[dict[str, str]] | None = None,
    ):
        settings = get_settings()
        self.task_lm_model = task_lm_model
        self.hire_threshold = hire_threshold or settings.hire_threshold
        self.job_id = job_id
        self.run_status = run_status
        self.job_description = job_description
        self.core_values = core_values or []

    def _update_eval_progress(self, completed: int, total: int) -> None:
        if self.job_id is None or self.run_status is None:
            return
        status = self.run_status.get(self.job_id)
        if status is None:
            return
        phase = status.get("phase")
        if phase in (None, "starting", "seed_evaluation"):
            status["phase"] = "seed_evaluation"
            status["seed_eval_completed"] = completed
            status["seed_eval_total"] = total

    def evaluate(
        self,
        batch: list[HiringDataInst],
        candidate: dict[str, str],
        capture_traces: bool = False,
    ) -> EvaluationBatch[HiringTrajectory, HiringRolloutOutput]:
        outputs: list[HiringRolloutOutput] = []
        scores: list[float] = []
        trajectories: list[HiringTrajectory] | None = [] if capture_traces else None
        batch_total = len(batch)

        if self.job_id is not None and self.run_status is not None:
            status = self.run_status.get(self.job_id)
            if status is not None and status.get("phase") in (None, "starting"):
                status["phase"] = "seed_evaluation"
                status["seed_eval_completed"] = 0
                status["seed_eval_total"] = batch_total

        for i, data in enumerate(batch):
            try:
                score, output, trajectory = _evaluate_single_resume(
                    data,
                    candidate,
                    task_lm_model=self.task_lm_model,
                    hire_threshold=self.hire_threshold,
                    job_description=self.job_description,
                    core_values=self.core_values,
                )
            except Exception as exc:
                score = 0.0
                output = {
                    "aggregate_score": 0.0,
                    "prediction": "Rejected",
                    "prompt_scores": {},
                }
                trajectory = None
                if capture_traces and trajectories is not None:
                    trajectories.append(
                        {
                            "data": data,
                            "prompt_results": {},
                            "aggregate_score": 0.0,
                            "prediction": "Rejected",
                            "expected_label": data["answer"],
                            "is_correct": False,
                            "feedback_by_prompt": {
                                key: f"Evaluation failed: {exc}" for key in PROMPT_KEYS
                            },
                        }
                    )
                outputs.append(output)
                scores.append(score)
                self._update_eval_progress(i + 1, batch_total)
                continue

            outputs.append(output)
            scores.append(score)
            if trajectories is not None and trajectory is not None:
                trajectories.append(trajectory)
            self._update_eval_progress(i + 1, batch_total)

        return EvaluationBatch(
            outputs=outputs,
            scores=scores,
            trajectories=trajectories,
            objective_scores=None,
        )

    def make_reflective_dataset(
        self,
        candidate: dict[str, str],
        eval_batch: EvaluationBatch[HiringTrajectory, HiringRolloutOutput],
        components_to_update: list[str],
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        if len(components_to_update) != 1:
            raise ValueError(
                f"HiringAdapter expects exactly one component to update, got {components_to_update}"
            )

        comp = components_to_update[0]
        trajectories = eval_batch.trajectories
        if trajectories is None:
            raise ValueError("Trajectories are required to build a reflective dataset.")

        items: list[HiringReflectiveRecord] = []
        for traj in trajectories:
            prompt_result = traj["prompt_results"].get(comp)
            generated = prompt_result["response_text"] if prompt_result else ""
            feedback = traj["feedback_by_prompt"].get(
                comp, "No feedback available for this prompt."
            )
            items.append(
                {
                    "Inputs": traj["data"]["input"][:2000],
                    "Generated Outputs": generated,
                    "Feedback": feedback,
                }
            )

        if not items:
            raise RuntimeError("No valid predictions found for reflective dataset.")

        return {comp: items}
