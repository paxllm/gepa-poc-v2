"""Tests for LLM seed candidate generation."""

import json
from unittest.mock import MagicMock, patch

from backend.gepa_integration.prompt_templates import compose_talent_lens_prompt
from backend.gepa_integration.seed_generator import (
    _parse_seed_response,
    generate_seed_candidate,
)

JD = "Senior Full Stack Engineer"
CV = [{"name": "Excellence", "description": "Ship quality code."}]
USER_PROMPTS = ["angle 1", "angle 2", "angle 3", "angle 4", "angle 5"]


def test_parse_seed_response_valid_json():
    payload = {f"prompt_{i}": f"Generated lens {i}" for i in range(1, 6)}
    result = _parse_seed_response(json.dumps(payload))
    assert result == payload


def test_parse_seed_response_strips_markdown_fences():
    payload = {f"prompt_{i}": f"Generated lens {i}" for i in range(1, 6)}
    fenced = f"```json\n{json.dumps(payload)}\n```"
    result = _parse_seed_response(fenced)
    assert result == payload


def test_parse_seed_response_strips_composed_wrappers():
    composed = compose_talent_lens_prompt("Inner lens text", JD, CV)
    payload = {
        "prompt_1": composed,
        **{f"prompt_{i}": f"Lens {i}" for i in range(2, 6)},
    }
    result = _parse_seed_response(json.dumps(payload))
    assert result["prompt_1"] == "Inner lens text"
    assert result["prompt_2"] == "Lens 2"


@patch("backend.gepa_integration.seed_generator.completion_with_retry")
def test_generate_seed_candidate_success(mock_completion):
    generated = {f"prompt_{i}": f"LLM lens {i}" for i in range(1, 6)}
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(generated)))]
    )

    result = generate_seed_candidate(
        USER_PROMPTS,
        job_description=JD,
        core_values=CV,
        task_lm_model="openai/test",
    )

    assert result == generated
    mock_completion.assert_called_once()


@patch("backend.gepa_integration.seed_generator.completion_with_retry")
def test_generate_seed_candidate_fallback_on_malformed_json(mock_completion):
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="not valid json"))]
    )

    result = generate_seed_candidate(
        USER_PROMPTS,
        job_description=JD,
        core_values=CV,
        task_lm_model="openai/test",
    )

    assert result == {f"prompt_{i + 1}": p for i, p in enumerate(USER_PROMPTS)}


@patch("backend.gepa_integration.seed_generator.completion_with_retry")
def test_generate_seed_candidate_fallback_on_missing_key(mock_completion):
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"prompt_1": "only one"}'))]
    )

    result = generate_seed_candidate(
        USER_PROMPTS,
        job_description=JD,
        core_values=CV,
        task_lm_model="openai/test",
    )

    assert result == {f"prompt_{i + 1}": p for i, p in enumerate(USER_PROMPTS)}
