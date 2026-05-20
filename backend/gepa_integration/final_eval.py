"""
Post-optimization evaluation on train, val, and test splits.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.gepa_integration.evaluator import evaluate_candidate_on_dataset
from backend.models.db_models import CandidatePrediction, IterationMetrics


async def run_final_evaluation(
    session: AsyncSession,
    *,
    job_id: int,
    candidate_set_id: str,
    best_candidate: dict[str, str],
    trainset: list[dict[str, Any]],
    valset: list[dict[str, Any]],
    testset: list[dict[str, Any]],
    hire_threshold: float,
    task_lm_model: str,
    job_description: str,
    core_values: list[dict[str, str]],
    stop_reason: str | None,
    final_iteration: int,
) -> dict[str, Any]:
    """
    Evaluate best candidate on all splits; persist final metrics and test predictions.
    """
    eval_kwargs = {
        "hire_threshold": hire_threshold,
        "task_lm_model": task_lm_model,
        "job_description": job_description,
        "core_values": core_values,
    }
    train_m = evaluate_candidate_on_dataset(best_candidate, trainset, **eval_kwargs)
    val_m = evaluate_candidate_on_dataset(best_candidate, valset, **eval_kwargs)
    test_m = evaluate_candidate_on_dataset(best_candidate, testset, **eval_kwargs)

    overfit_gap = train_m["accuracy"] - val_m["accuracy"]

    for outcome in test_m["outcomes"]:
        if outcome["resume_id"] is None:
            continue
        session.add(
            CandidatePrediction(
                resume_id=outcome["resume_id"],
                candidate_set_id=candidate_set_id,
                iteration=final_iteration,
                aggregate_score=outcome["aggregate_score"],
                prediction=outcome["prediction"],
                actual_label=outcome["actual_label"],
                is_correct=outcome["is_correct"],
            )
        )

    metrics = IterationMetrics(
        job_id=job_id,
        candidate_set_id=candidate_set_id,
        iteration=final_iteration,
        accuracy=val_m["accuracy"],
        val_accuracy=val_m["accuracy"],
        train_accuracy=train_m["accuracy"],
        test_accuracy=test_m["accuracy"],
        overfit_gap=overfit_gap,
        stop_reason=stop_reason,
        precision_val=test_m["precision_val"],
        recall=test_m["recall"],
        f1_score=test_m["f1_score"],
        true_positives=test_m["true_positives"],
        false_positives=test_m["false_positives"],
        true_negatives=test_m["true_negatives"],
        false_negatives=test_m["false_negatives"],
    )
    session.add(metrics)

    return {
        "train_accuracy": train_m["accuracy"],
        "val_accuracy": val_m["accuracy"],
        "test_accuracy": test_m["accuracy"],
        "overfit_gap": overfit_gap,
        "stop_reason": stop_reason,
    }
