"""
LLM-based seed candidate generation at GEPA launch.
"""

from __future__ import annotations

import json
import logging
import re

from backend.core.config import get_settings
from backend.core.litellm_client import completion_with_retry, get_llm_timeout
from backend.gepa_integration.prompt_templates import (
    build_seed_candidate,
    build_seed_generation_messages,
    normalize_prompts,
)

logger = logging.getLogger(__name__)

PROMPT_KEYS = tuple(f"prompt_{i}" for i in range(1, 6))
def _strip_json_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _parse_seed_response(response_text: str) -> dict[str, str]:
    cleaned = _strip_json_fences(response_text)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Seed generation response must be a JSON object")

    result: dict[str, str] = {}
    for key in PROMPT_KEYS:
        if key not in parsed:
            raise ValueError(f"Missing key {key} in seed generation response")
        value = parsed[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Key {key} must be a non-empty string")
        result[key] = value.strip()

    normalized_values = normalize_prompts(list(result.values()))
    return {key: normalized_values[i] for i, key in enumerate(PROMPT_KEYS)}


def generate_seed_candidate(
    user_prompts: list[str],
    job_description: str,
    core_values: list[dict[str, str]],
    task_lm_model: str,
) -> dict[str, str]:
    """
    Generate 5 tailored evaluation lenses via LLM, falling back to user prompts on failure.
    When demo_mode is enabled, user prompts are used directly without an LLM call.
    """
    if get_settings().demo_mode:
        logger.info("Demo mode active: using user prompts directly as seed candidate")
        return build_seed_candidate(
            user_prompts,
            job_description=job_description,
            core_values=core_values,
        )

    fallback = build_seed_candidate(
        user_prompts,
        job_description=job_description,
        core_values=core_values,
    )

    messages = build_seed_generation_messages(
        user_prompts, job_description, core_values
    )

    try:
        completion = completion_with_retry(
            model=task_lm_model,
            messages=messages,
            timeout=get_llm_timeout(),
        )
        response_text = completion.choices[0].message.content or ""
        return _parse_seed_response(response_text)
    except Exception as exc:
        logger.warning(
            "LLM seed generation failed, using user prompts as fallback: %s", exc
        )
        return fallback
