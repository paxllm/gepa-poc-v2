"""
GEPA optimization runner.
Orchestrates the end-to-end flow:
1. Assign train/val/test splits and build datasets
2. Create seed candidate from user's 5 prompts
3. Call gepa.optimize() with held-out valset and early stopping
4. Persist per-iteration and final evaluation results
"""

import asyncio
import json
import uuid
from functools import partial
from pathlib import Path
from typing import Any

import gepa
from gepa import NoImprovementStopper
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.database import get_session_factory
from backend.core.encoding import ensure_utf8_environment
from backend.core.litellm_client import configure_litellm, make_reflection_lm
from backend.gepa_integration.dataset_split import assign_splits
from backend.gepa_integration.hiring_adapter import HiringAdapter
from backend.gepa_integration.final_eval import run_final_evaluation
from backend.gepa_integration.metrics_callback import MetricsPersistenceCallback
from backend.gepa_integration.seed_generator import generate_seed_candidate
from backend.models.db_models import (
    CoreValue,
    IterationMetrics,
    Job,
    PromptEvolutionLog,
    Resume,
    TalentLens,
)


# Global state for tracking optimization runs
_run_status: dict[int, dict[str, Any]] = {}


def get_run_status(job_id: int) -> dict[str, Any]:
    """Get the current status of an optimization run."""
    return _run_status.get(job_id, {"status": "idle"})


def resolve_optimization_params(
    max_metric_calls: int | None,
    hire_threshold: float | None,
    early_stop_patience: int | None,
) -> tuple[int, float, int]:
    """Apply server defaults only when a parameter was omitted (null)."""
    settings = get_settings()
    if max_metric_calls is None:
        max_metric_calls = settings.gepa_max_metric_calls
    if hire_threshold is None:
        hire_threshold = settings.hire_threshold
    if early_stop_patience is None:
        early_stop_patience = settings.early_stop_patience
    return max_metric_calls, hire_threshold, early_stop_patience


def init_run_status(
    job_id: int,
    *,
    run_set_id: str,
    max_metric_calls: int,
    hire_threshold: float,
) -> None:
    """Mark a job as running with resolved config before the background task starts."""
    _run_status[job_id] = {
        "status": "running",
        "current_iteration": 0,
        "best_candidate_set_id": run_set_id,
        "run_candidate_set_id": run_set_id,
        "total_metric_calls": 0,
        "max_metric_calls": max_metric_calls,
        "hire_threshold": hire_threshold,
        "phase": "starting",
        "live_eval_outcomes": [],
    }


class _ReasonTrackingStopper:
    """Wraps a GEPA stopper and records why optimization stopped."""

    def __init__(self, stopper: Any, reason: str, holder: dict[str, str]):
        self._stopper = stopper
        self._reason = reason
        self._holder = holder

    def __call__(self, gepa_state: Any) -> bool:
        if self._stopper(gepa_state):
            self._holder["reason"] = self._reason
            return True
        return False


def _infer_stop_reason(
    *,
    holder: dict[str, str],
    total_metric_calls: int | None,
    max_metric_calls: int,
    run_dir: str | None,
    no_improve_stopper: NoImprovementStopper,
    early_stop_patience: int,
) -> str:
    if holder.get("reason") == "no_improvement":
        return "no_improvement"
    if run_dir and Path(run_dir, "gepa.stop").exists():
        return "manual_stop"
    if (
        no_improve_stopper.iterations_without_improvement >= early_stop_patience
        and holder.get("reason") != "max_metric_calls"
    ):
        return "no_improvement"
    if total_metric_calls is not None and total_metric_calls >= max_metric_calls:
        return "max_metric_calls"
    return holder.get("reason", "completed")


async def build_dataset(
    session: AsyncSession,
    job_id: int,
    split: str,
) -> list[dict[str, Any]]:
    """
    Build a GEPA-compatible dataset for a given split (train / val / test).
    """
    job_result = await session.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one()

    cv_result = await session.execute(
        select(CoreValue).where(CoreValue.job_id == job_id)
    )
    core_values = [
        {"name": cv.name, "description": cv.description}
        for cv in cv_result.scalars().all()
    ]

    resume_result = await session.execute(
        select(Resume).where(
            Resume.job_id == job_id,
            Resume.dataset_split == split,
            Resume.parsed_text.is_not(None),
        )
    )
    resumes = resume_result.scalars().all()

    dataset: list[dict[str, Any]] = []
    for resume in resumes:
        dataset.append({
            "input": resume.parsed_text,
            "additional_context": {
                "job_description": job.description,
                "core_values_json": json.dumps(core_values),
                "candidate_name": resume.candidate_name,
                "resume_id": str(resume.id),
                "dataset_split": split,
            },
            "answer": resume.hiring_label,
        })

    return dataset


async def run_optimization(
    job_id: int,
    prompts: list[str],
    max_metric_calls: int | None = None,
    hire_threshold: float | None = None,
    early_stop_patience: int | None = None,
    force_resplit: bool = False,
) -> dict[str, Any]:
    """Run the full GEPA optimization loop with held-out validation and early stopping."""
    settings = get_settings()
    max_metric_calls, hire_threshold, early_stop_patience = resolve_optimization_params(
        max_metric_calls, hire_threshold, early_stop_patience
    )

    factory = get_session_factory()
    existing = _run_status.get(job_id, {})
    if existing.get("status") == "running" and existing.get("run_candidate_set_id"):
        run_set_id = existing["run_candidate_set_id"]
    else:
        run_set_id = f"run_{uuid.uuid4().hex[:8]}"
        init_run_status(
            job_id,
            run_set_id=run_set_id,
            max_metric_calls=max_metric_calls,
            hire_threshold=hire_threshold,
        )
    run_dir = str(settings.data_dir / "gepa_runs" / f"job_{job_id}")

    try:
        async with factory() as session:
            await session.execute(
                update(TalentLens)
                .where(
                    TalentLens.job_id == job_id,
                    TalentLens.generation == "evolved",
                    TalentLens.is_active.is_(True),
                )
                .values(is_active=False)
            )
            await session.execute(
                delete(IterationMetrics).where(
                    IterationMetrics.job_id == job_id,
                    IterationMetrics.iteration >= 0,
                )
            )
            await session.execute(
                delete(PromptEvolutionLog).where(PromptEvolutionLog.job_id == job_id)
            )
            await session.commit()

            split_summary = await assign_splits(
                session, job_id, force_resplit=force_resplit
            )
            trainset = await build_dataset(session, job_id, "train")
            valset = await build_dataset(session, job_id, "val")
            testset = await build_dataset(session, job_id, "test")

        if not trainset or not valset or not testset:
            raise ValueError(
                "Train, val, and test sets must each have at least one resume. "
                "Upload more resumes or force a resplit."
            )

        _run_status[job_id]["split_summary"] = {
            "train": split_summary["train"],
            "val": split_summary["val"],
            "test": split_summary["test"],
        }

        async with factory() as session:
            job_result = await session.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one()

            cv_result = await session.execute(
                select(CoreValue).where(CoreValue.job_id == job_id)
            )
            core_values = [
                {"name": cv.name, "description": cv.description}
                for cv in cv_result.scalars().all()
            ]

        _run_status[job_id]["phase"] = "generating_seed"
        ensure_utf8_environment()
        task_lm_model = configure_litellm()

        seed_candidate = generate_seed_candidate(
            user_prompts=prompts,
            job_description=job.description,
            core_values=core_values,
            task_lm_model=task_lm_model,
        )
        seed_set_id = f"seed_{uuid.uuid4().hex[:8]}"

        async with factory() as session:
            for idx in range(5):
                prompt_key = f"prompt_{idx + 1}"
                session.add(
                    TalentLens(
                        job_id=job_id,
                        candidate_set_id=seed_set_id,
                        prompt_index=idx + 1,
                        prompt_text=seed_candidate[prompt_key],
                        iteration=0,
                        generation="seed",
                    )
                )
            await session.commit()

        _run_status[job_id]["seed_candidate_set_id"] = seed_set_id

        adapter = HiringAdapter(
            task_lm_model=task_lm_model,
            hire_threshold=hire_threshold,
            job_id=job_id,
            run_status=_run_status,
            job_description=job.description,
            core_values=core_values,
        )

        loop = asyncio.get_running_loop()
        metrics_callback = MetricsPersistenceCallback(
            job_id=job_id,
            candidate_set_id=run_set_id,
            session_factory=factory,
            loop=loop,
            run_status=_run_status,
        )

        stop_holder: dict[str, str] = {"reason": "completed"}
        no_improve_stopper = NoImprovementStopper(early_stop_patience)
        tracked_no_improve = _ReasonTrackingStopper(
            no_improve_stopper, "no_improvement", stop_holder
        )

        reflection_lm = make_reflection_lm(task_lm_model)

        result = await loop.run_in_executor(
            None,
            partial(
                gepa.optimize,
                seed_candidate=seed_candidate,
                trainset=trainset,
                valset=valset,
                adapter=adapter,
                reflection_lm=reflection_lm,
                max_metric_calls=max_metric_calls,
                stop_callbacks=tracked_no_improve,
                candidate_selection_strategy="pareto",
                display_progress_bar=True,
                run_dir=run_dir,
                callbacks=[metrics_callback],
                seed=settings.gepa_seed,
            ),
        )

        best_candidate = result.best_candidate
        best_score = (
            result.val_aggregate_scores[result.best_idx]
            if result.val_aggregate_scores
            else 0.0
        )

        stop_reason = _infer_stop_reason(
            holder=stop_holder,
            total_metric_calls=result.total_metric_calls,
            max_metric_calls=max_metric_calls,
            run_dir=run_dir,
            no_improve_stopper=no_improve_stopper,
            early_stop_patience=early_stop_patience,
        )

        best_set_id = f"best_{uuid.uuid4().hex[:8]}"
        final_iteration = -1

        async with factory() as session:
            for key, prompt_text in best_candidate.items():
                idx = int(key.split("_")[1])
                session.add(
                    TalentLens(
                        job_id=job_id,
                        candidate_set_id=best_set_id,
                        prompt_index=idx,
                        prompt_text=prompt_text,
                        iteration=-1,
                        generation="evolved",
                        fitness_score=best_score,
                        is_active=True,
                    )
                )

            try:
                eval_summary = await run_final_evaluation(
                    session,
                    job_id=job_id,
                    candidate_set_id=best_set_id,
                    best_candidate=best_candidate,
                    trainset=trainset,
                    valset=valset,
                    testset=testset,
                    hire_threshold=hire_threshold,
                    task_lm_model=task_lm_model,
                    job_description=job.description,
                    core_values=core_values,
                    stop_reason=stop_reason,
                    final_iteration=final_iteration,
                )
            except Exception as eval_exc:
                eval_summary = {
                    "train_accuracy": None,
                    "val_accuracy": best_score,
                    "test_accuracy": None,
                    "overfit_gap": None,
                    "stop_reason": stop_reason,
                    "final_eval_error": str(eval_exc),
                }
            await session.commit()

        _run_status[job_id] = {
            "status": "completed",
            "best_accuracy": best_score,
            "best_candidate_set_id": best_set_id,
            "seed_candidate_set_id": seed_set_id,
            "split_summary": _run_status[job_id].get("split_summary"),
            "stop_reason": stop_reason,
            "overfit_gap": eval_summary.get("overfit_gap"),
            "train_accuracy": eval_summary.get("train_accuracy"),
            "test_accuracy": eval_summary.get("test_accuracy"),
            "total_metric_calls": result.total_metric_calls,
            "max_metric_calls": max_metric_calls,
            "hire_threshold": hire_threshold,
            "final_eval_error": eval_summary.get("final_eval_error"),
        }

        return {
            "status": "completed",
            "best_candidate": best_candidate,
            "best_score": best_score,
            "best_candidate_set_id": best_set_id,
            "stop_reason": stop_reason,
            "overfit_gap": eval_summary["overfit_gap"],
            "test_accuracy": eval_summary["test_accuracy"],
        }

    except Exception as e:
        _run_status[job_id] = {
            "status": "error",
            "error_message": str(e),
        }
        raise
