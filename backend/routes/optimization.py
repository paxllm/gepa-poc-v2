"""
Optimization endpoints: start, status, and results.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.gepa_integration.runner import get_run_status, run_optimization
from backend.gepa_integration.prompt_templates import normalize_prompts
from backend.models.db_models import (
    CandidatePrediction,
    IterationMetrics,
    Job,
    PromptEvolutionLog,
    Resume,
    TalentLens,
)
from backend.models.schemas import (
    InterimPromptResponse,
    IterationMetricsResponse,
    OptimizationRequest,
    OptimizationStatusResponse,
    PromptEvolutionResponse,
    SplitSummaryResponse,
    TalentLensResponse,
)

router = APIRouter(prefix="/api/jobs/{job_id}", tags=["optimization"])


def _run_optimization_sync(
    job_id: int,
    prompts: list[str],
    max_metric_calls: int | None,
    hire_threshold: float | None,
    early_stop_patience: int | None,
    force_resplit: bool,
):
    """Wrapper to run async optimization in a new event loop for background tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            run_optimization(
                job_id=job_id,
                prompts=prompts,
                max_metric_calls=max_metric_calls,
                hire_threshold=hire_threshold,
                early_stop_patience=early_stop_patience,
                force_resplit=force_resplit,
            )
        )
    finally:
        loop.close()


async def _get_split_summary(db: AsyncSession, job_id: int) -> SplitSummaryResponse:
    result = await db.execute(
        select(Resume).where(Resume.job_id == job_id, Resume.parsed_text.is_not(None))
    )
    resumes = result.scalars().all()
    train_c = sum(1 for r in resumes if r.dataset_split == "train")
    val_c = sum(1 for r in resumes if r.dataset_split == "val")
    test_c = sum(1 for r in resumes if r.dataset_split == "test")
    assigned = bool(resumes) and all(
        r.dataset_split in ("train", "val", "test") for r in resumes
    )
    return SplitSummaryResponse(
        train=train_c,
        val=val_c,
        test=test_c,
        total=len(resumes),
        assigned=assigned,
    )


@router.get("/split-summary", response_model=SplitSummaryResponse)
async def get_split_summary(job_id: int, db: AsyncSession = Depends(get_db)):
    """Return train/val/test counts and whether splits are assigned."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    return await _get_split_summary(db, job_id)


@router.post("/optimize", response_model=OptimizationStatusResponse, status_code=202)
async def start_optimization(
    job_id: int,
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a GEPA optimization run with held-out validation."""
    settings = get_settings()

    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    resume_result = await db.execute(
        select(Resume).where(Resume.job_id == job_id, Resume.parsed_text.is_not(None))
    )
    resumes = resume_result.scalars().all()
    if len(resumes) < settings.min_resumes_for_split:
        raise HTTPException(
            status_code=400,
            detail=(
                f"At least {settings.min_resumes_for_split} parsed resumes are required "
                f"for optimization (got {len(resumes)})"
            ),
        )

    current_status = get_run_status(job_id)
    if current_status.get("status") == "running":
        raise HTTPException(
            status_code=409,
            detail="Optimization is already running for this job",
        )

    prompts = normalize_prompts([p.prompt_text for p in request.prompts.prompts])
    split_summary = await _get_split_summary(db, job_id)

    background_tasks.add_task(
        _run_optimization_sync,
        job_id=job_id,
        prompts=prompts,
        max_metric_calls=request.max_metric_calls,
        hire_threshold=request.hire_threshold,
        early_stop_patience=request.early_stop_patience,
        force_resplit=request.force_resplit,
    )

    return OptimizationStatusResponse(
        status="running",
        current_iteration=0,
        split_summary=split_summary,
    )


@router.get("/optimize/status", response_model=OptimizationStatusResponse)
async def get_optimization_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get the current status of an optimization run."""
    status = get_run_status(job_id)
    split_summary = None
    if status.get("split_summary"):
        s = status["split_summary"]
        split_summary = SplitSummaryResponse(
            train=s["train"],
            val=s["val"],
            test=s["test"],
            total=s["train"] + s["val"] + s["test"],
            assigned=True,
        )
    else:
        split_summary = await _get_split_summary(db, job_id)

    metrics_history = None
    if status.get("status") == "running":
        run_set_id = status.get("run_candidate_set_id")
        metrics_query = (
            select(IterationMetrics)
            .where(IterationMetrics.job_id == job_id, IterationMetrics.iteration >= 0)
            .order_by(IterationMetrics.iteration)
        )
        if run_set_id:
            metrics_query = metrics_query.where(
                IterationMetrics.candidate_set_id == run_set_id
            )
        metrics_result = await db.execute(metrics_query)
        metrics_history = metrics_result.scalars().all()

    interim_raw = status.get("interim_best_prompts")
    interim_best_prompts = (
        [InterimPromptResponse.model_validate(p) for p in interim_raw]
        if interim_raw
        else None
    )

    return OptimizationStatusResponse(
        status=status.get("status", "idle"),
        phase=status.get("phase"),
        seed_eval_completed=status.get("seed_eval_completed"),
        seed_eval_total=status.get("seed_eval_total"),
        max_metric_calls=status.get("max_metric_calls"),
        current_iteration=status.get("current_iteration"),
        total_metric_calls=status.get("total_metric_calls"),
        best_accuracy=status.get("best_accuracy"),
        error_message=status.get("error_message"),
        stop_reason=status.get("stop_reason"),
        overfit_gap=status.get("overfit_gap"),
        train_accuracy=status.get("train_accuracy"),
        test_accuracy=status.get("test_accuracy"),
        split_summary=split_summary,
        metrics_history=(
            [IterationMetricsResponse.model_validate(m) for m in metrics_history]
            if metrics_history is not None
            else None
        ),
        interim_best_prompts=interim_best_prompts,
    )


@router.get("/results")
async def get_optimization_results(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the full results of a completed optimization run."""
    status = get_run_status(job_id)
    is_running = status.get("status") == "running"
    run_set_id = status.get("run_candidate_set_id")
    seed_set_id = status.get("seed_candidate_set_id")

    lens_result = await db.execute(
        select(TalentLens)
        .where(TalentLens.job_id == job_id, TalentLens.generation == "evolved")
        .order_by(TalentLens.created_at.desc())
    )
    best_lenses = list(lens_result.scalars().all())
    if is_running:
        best_lenses = []

    all_lens_result = await db.execute(
        select(TalentLens)
        .where(TalentLens.job_id == job_id)
        .order_by(TalentLens.created_at)
    )
    all_lenses = list(all_lens_result.scalars().all())
    if is_running and run_set_id:
        interim_id = f"{run_set_id}_interim"
        allowed_ids = {run_set_id, interim_id}
        if seed_set_id:
            allowed_ids.add(seed_set_id)
        all_lenses = [l for l in all_lenses if l.candidate_set_id in allowed_ids]

    metrics_result = await db.execute(
        select(IterationMetrics)
        .where(IterationMetrics.job_id == job_id)
        .order_by(IterationMetrics.iteration)
    )
    metrics = metrics_result.scalars().all()

    evo_result = await db.execute(
        select(PromptEvolutionLog)
        .where(PromptEvolutionLog.job_id == job_id)
        .order_by(PromptEvolutionLog.iteration)
    )
    evolution_log = evo_result.scalars().all()

    predictions_result = await db.execute(
        select(CandidatePrediction)
        .join(Resume, CandidatePrediction.resume_id == Resume.id)
        .where(Resume.job_id == job_id)
        .order_by(CandidatePrediction.id)
    )
    predictions = list(predictions_result.scalars().all())
    if is_running:
        predictions = []

    split_summary = await _get_split_summary(db, job_id)

    final_metrics = (
        None
        if is_running
        else next((m for m in reversed(metrics) if m.iteration == -1), None)
    )
    iteration_metrics = [m for m in metrics if m.iteration >= 0]
    if is_running and run_set_id:
        iteration_metrics = [m for m in iteration_metrics if m.candidate_set_id == run_set_id]

    if is_running:
        stop_reason = status.get("stop_reason")
        overfit_gap = status.get("overfit_gap")
        train_accuracy = status.get("train_accuracy")
        test_accuracy = status.get("test_accuracy")
    else:
        stop_reason = status.get("stop_reason") or (
            final_metrics.stop_reason if final_metrics else None
        )
        overfit_gap = status.get("overfit_gap") or (
            final_metrics.overfit_gap if final_metrics else None
        )
        train_accuracy = status.get("train_accuracy") or (
            final_metrics.train_accuracy if final_metrics else None
        )
        test_accuracy = status.get("test_accuracy") or (
            final_metrics.test_accuracy if final_metrics else None
        )

    return {
        "status": status.get("status", "idle"),
        "phase": status.get("phase"),
        "seed_eval_completed": status.get("seed_eval_completed"),
        "seed_eval_total": status.get("seed_eval_total"),
        "max_metric_calls": status.get("max_metric_calls"),
        "best_candidate_set_id": status.get("best_candidate_set_id"),
        "best_accuracy": status.get("best_accuracy"),
        "stop_reason": stop_reason,
        "overfit_gap": overfit_gap,
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "split_summary": SplitSummaryResponse.model_validate(split_summary).model_dump(),
        "overfit_gap_threshold": get_settings().overfit_gap_threshold,
        "best_prompts": [TalentLensResponse.model_validate(lens) for lens in best_lenses],
        "all_prompts": [TalentLensResponse.model_validate(lens) for lens in all_lenses],
        "metrics_history": [
            IterationMetricsResponse.model_validate(m) for m in iteration_metrics
        ],
        "final_metrics": (
            IterationMetricsResponse.model_validate(final_metrics)
            if final_metrics
            else None
        ),
        "evolution_log": [
            PromptEvolutionResponse.model_validate(e) for e in evolution_log
        ],
        "test_predictions": [
            {
                "id": p.id,
                "resume_id": p.resume_id,
                "candidate_set_id": p.candidate_set_id,
                "aggregate_score": p.aggregate_score,
                "prediction": p.prediction,
                "actual_label": p.actual_label,
                "is_correct": p.is_correct,
            }
            for p in predictions
        ],
    }


@router.get("/metrics", response_model=list[IterationMetricsResponse])
async def get_metrics(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get iteration-level metrics for a job (excludes final summary row)."""
    result = await db.execute(
        select(IterationMetrics)
        .where(IterationMetrics.job_id == job_id, IterationMetrics.iteration >= 0)
        .order_by(IterationMetrics.iteration)
    )
    return result.scalars().all()


@router.get("/evolution", response_model=list[PromptEvolutionResponse])
async def get_evolution_log(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get prompt evolution history for a job."""
    result = await db.execute(
        select(PromptEvolutionLog)
        .where(PromptEvolutionLog.job_id == job_id)
        .order_by(PromptEvolutionLog.iteration)
    )
    return result.scalars().all()
