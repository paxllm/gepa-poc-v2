"""
Live scoring endpoint: score a new (unlabeled) candidate against the
job's currently-active best prompt set.
"""

import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.litellm_client import configure_litellm
from backend.core import usage_tracker
from backend.models.db_models import LLMUsageLog
from backend.gepa_integration.hiring_adapter import score_resume
from backend.gepa_integration.prompt_loader import load_active_candidate
from backend.models.db_models import (
    CandidatePrediction,
    CoreValue,
    Job,
    Resume,
)
from backend.models.schemas import PromptScoreDetail, ScoreCandidateResponse
from backend.parser.resume_parser import parse_resume


router = APIRouter(prefix="/api/jobs/{job_id}", tags=["scoring"])


@router.post(
    "/candidates/score",
    response_model=ScoreCandidateResponse,
    status_code=201,
)
async def score_candidate(
    job_id: int,
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Score a new candidate against the active best prompt set."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ("pdf", "docx", "txt"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use PDF, DOCX, or TXT.",
        )

    active = await load_active_candidate(db, job_id)
    if active is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "No prompt set is available for this job yet. "
                "Complete the setup wizard and run /optimize first."
            ),
        )
    candidate_set_id, candidate = active

    settings = get_settings()
    file_id = uuid.uuid4().hex[:12]
    file_name = f"{file_id}_{file.filename}"
    file_path = settings.upload_path / file_name
    with open(file_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        parsed_text = parse_resume(file_path)
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {exc}")

    cv_result = await db.execute(select(CoreValue).where(CoreValue.job_id == job_id))
    core_values = [
        {"name": cv.name, "description": cv.description}
        for cv in cv_result.scalars().all()
    ]

    task_lm_model = configure_litellm()
    try:
        result = score_resume(
            parsed_text,
            candidate,
            task_lm_model=task_lm_model,
            hire_threshold=settings.hire_threshold,
            job_description=job.description,
            core_values=core_values,
            job_id=job_id,
            run_set_id=candidate_set_id,
        )
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=f"Scoring failed: {exc}")

    # Flush any usage records collected during scoring to the DB
    nim_model = settings.nvidia_model
    for rec in usage_tracker.drain_pending():
        db.add(LLMUsageLog(
            job_id=rec.job_id if rec.job_id is not None else job_id,
            run_set_id=rec.run_set_id or candidate_set_id,
            call_type=rec.call_type,
            model=rec.model,
            prompt_tokens=rec.prompt_tokens,
            completion_tokens=rec.completion_tokens,
            total_tokens=rec.total_tokens,
        ))

    resume = Resume(
        job_id=job_id,
        candidate_name=candidate_name,
        file_path=str(file_path),
        file_type=suffix,
        parsed_text=parsed_text,
        hiring_label=None,
        status="pending_decision",
        entry_source="live",
        dataset_split=None,
    )
    db.add(resume)
    await db.flush()

    prediction = CandidatePrediction(
        resume_id=resume.id,
        candidate_set_id=candidate_set_id,
        iteration=-1,
        aggregate_score=result["aggregate_score"],
        prediction=result["prediction"],
        actual_label=None,
        is_correct=None,
    )
    db.add(prediction)
    await db.flush()

    prompt_scores = [
        PromptScoreDetail(
            prompt_index=int(key.split("_")[1]),
            score=result["prompt_results"][key]["score"],
            rationale=result["prompt_results"][key]["rationale"],
        )
        for key in sorted(result["prompt_results"].keys())
    ]

    return ScoreCandidateResponse(
        resume_id=resume.id,
        candidate_name=candidate_name,
        aggregate_score=result["aggregate_score"],
        prediction=result["prediction"],
        hire_threshold=settings.hire_threshold,
        candidate_set_id_used=candidate_set_id,
        prompt_scores=prompt_scores,
    )
