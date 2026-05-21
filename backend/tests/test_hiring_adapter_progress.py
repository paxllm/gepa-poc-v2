"""Tests for HiringAdapter progress reporting and parallel prompt evaluation."""

from unittest.mock import MagicMock, patch

from backend.gepa_integration.hiring_adapter import (
    HiringAdapter,
    _evaluate_one_prompt,
)


def test_evaluate_updates_seed_progress():
    run_status: dict[int, dict] = {
        1: {"status": "running", "phase": "starting"},
    }
    adapter = HiringAdapter(
        task_lm_model="openai/test",
        hire_threshold=3.0,
        job_id=1,
        run_status=run_status,
    )

    batch = [
        {
            "input": "resume one",
            "additional_context": {
                "candidate_name": "Alice",
                "resume_id": "1",
                "dataset_split": "val",
            },
            "answer": "Hired",
        },
        {
            "input": "resume two",
            "additional_context": {
                "candidate_name": "Bob",
                "resume_id": "2",
                "dataset_split": "val",
            },
            "answer": "Rejected",
        },
    ]
    candidate = {f"prompt_{i}": f"lens {i}" for i in range(1, 6)}

    fake_result = {
        "score": 4.0,
        "rationale": "ok",
        "response_text": '{"score": 4, "rationale": "ok"}',
    }

    with patch(
        "backend.gepa_integration.hiring_adapter._evaluate_single_resume",
        side_effect=[
            (1.0, {"aggregate_score": 4.0, "prediction": "Hired", "prompt_scores": {}}, None),
            (1.0, {"aggregate_score": 2.0, "prediction": "Rejected", "prompt_scores": {}}, None),
        ],
    ):
        adapter.evaluate(batch, candidate)

    assert run_status[1]["phase"] == "seed_evaluation"
    assert run_status[1]["seed_eval_completed"] == 2
    assert run_status[1]["seed_eval_total"] == 2

    outcomes = run_status[1]["live_eval_outcomes"]
    assert len(outcomes) == 2
    assert outcomes[0]["candidate_name"] == "Alice"
    assert outcomes[0]["prediction"] == "Hired"
    assert outcomes[0]["actual_label"] == "Hired"
    assert outcomes[0]["is_correct"] is True
    assert outcomes[0]["split"] == "val"
    assert outcomes[1]["candidate_name"] == "Bob"
    assert outcomes[1]["actual_label"] == "Rejected"
    assert run_status[1]["best_accuracy"] == 1.0


def test_evaluate_syncs_live_val_accuracy():
    run_status: dict[int, dict] = {
        1: {"status": "running", "phase": "seed_evaluation", "best_accuracy": 1.0},
    }
    adapter = HiringAdapter(
        task_lm_model="openai/test",
        hire_threshold=3.0,
        job_id=1,
        run_status=run_status,
    )
    batch = [
        {
            "input": "resume",
            "additional_context": {
                "candidate_name": "Wrong",
                "resume_id": "1",
                "dataset_split": "train",
            },
            "answer": "Hired",
        },
    ]
    candidate = {f"prompt_{i}": f"lens {i}" for i in range(1, 6)}

    with patch(
        "backend.gepa_integration.hiring_adapter._evaluate_single_resume",
        return_value=(
            0.0,
            {"aggregate_score": 2.0, "prediction": "Rejected", "prompt_scores": {}},
            None,
        ),
    ):
        adapter.evaluate(batch, candidate)

    assert run_status[1]["best_accuracy"] == 0.0


def test_evaluate_records_error_outcome_without_fake_zero_score():
    run_status: dict[int, dict] = {
        1: {"status": "running", "phase": "seed_evaluation"},
    }
    adapter = HiringAdapter(
        task_lm_model="openai/test",
        hire_threshold=3.0,
        job_id=1,
        run_status=run_status,
    )
    batch = [
        {
            "input": "resume",
            "additional_context": {
                "candidate_name": "Fail",
                "resume_id": "9",
                "dataset_split": "val",
            },
            "answer": "Rejected",
        },
    ]
    candidate = {f"prompt_{i}": f"lens {i}" for i in range(1, 6)}

    with patch(
        "backend.gepa_integration.hiring_adapter._evaluate_single_resume",
        side_effect=RuntimeError("rate limited"),
    ):
        adapter.evaluate(batch, candidate)

    outcome = run_status[1]["live_eval_outcomes"][0]
    assert outcome["aggregate_score"] is None
    assert outcome["eval_error"] == "rate limited"
    assert "best_accuracy" not in run_status[1]


@patch("backend.gepa_integration.hiring_adapter.completion_with_retry")
def test_evaluate_one_prompt_calls_litellm_with_timeout(mock_completion):
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"score": 4, "rationale": "good"}'))]
    )
    _, result = _evaluate_one_prompt(
        "prompt_1",
        {"prompt_1": "Evaluate leadership"},
        "Jane Doe resume text",
        task_lm_model="openai/test",
        hire_threshold=3.0,
        job_description="Senior Engineer role",
        core_values=[{"name": "Excellence", "description": "Ship quality code."}],
    )
    mock_completion.assert_called_once()
    assert mock_completion.call_args.kwargs["timeout"] == 300
    assert result["score"] == 4.0
