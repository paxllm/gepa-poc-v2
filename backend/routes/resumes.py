"""
Resume upload / listing / decision endpoints.
"""

import base64
import datetime
import shutil
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.gepa_integration.prompt_loader import load_active_candidate
from backend.gepa_integration.runner import (
    get_run_status,
    run_optimization_in_background,
)
from backend.models.db_models import (
    CandidatePrediction,
    Job,
    Resume,
    TalentLens,
)
from backend.models.schemas import (
    BatchResumesUploadRequest,
    BatchResumesUploadResponse,
    BatchResumeUploadResult,
    DecisionRequest,
    DecisionResponse,
    PendingCandidateResponse,
    ResumeResponse,
    TrainingStatusResponse,
)
from backend.parser.resume_parser import parse_resume

router = APIRouter(prefix="/api/jobs/{job_id}", tags=["resumes"])


async def _decisions_since_last_train(db: AsyncSession, job: Job) -> int:
    """Count live decisions recorded after the most recent successful train."""
    stmt = select(func.count(Resume.id)).where(
        Resume.job_id == job.id,
        Resume.status == "decided",
        Resume.entry_source == "live",
        Resume.decision_made_at.is_not(None),
    )
    if job.last_optimized_at is not None:
        stmt = stmt.where(Resume.decision_made_at > job.last_optimized_at)
    result = await db.execute(stmt)
    return int(result.scalar_one())


@router.post("/resumes", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    job_id: int,
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    hiring_label: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a historical resume with its hiring label (wizard / bulk import)."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    if hiring_label not in ("Hired", "Rejected"):
        raise HTTPException(
            status_code=400, detail="hiring_label must be 'Hired' or 'Rejected'"
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ("pdf", "docx", "txt"):
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT."
        )

    settings = get_settings()
    file_id = uuid.uuid4().hex[:12]
    file_name = f"{file_id}_{file.filename}"
    file_path = settings.upload_path / file_name
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        parsed_text = parse_resume(file_path)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {e}")

    resume = Resume(
        job_id=job_id,
        candidate_name=candidate_name,
        file_path=str(file_path),
        file_type=suffix,
        parsed_text=parsed_text,
        hiring_label=hiring_label,
        status="decided",
        entry_source="historical",
        decision_made_at=datetime.datetime.utcnow(),
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


@router.get("/resumes", response_model=list[ResumeResponse])
async def list_resumes(job_id: int, db: AsyncSession = Depends(get_db)):
    """List all resumes for a job."""
    result = await db.execute(select(Resume).where(Resume.job_id == job_id))
    return result.scalars().all()


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume(job_id: int, resume_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific resume with its parsed text."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.job_id == job_id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post(
    "/resumes/{resume_id}/decision", response_model=DecisionResponse, status_code=200
)
async def record_decision(
    job_id: int,
    resume_id: int,
    body: DecisionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Record a hire/reject decision on a previously-scored candidate.

    Auto-triggers a warm-started retrain when the number of live decisions
    recorded since the last successful optimization reaches the job's
    `auto_retrain_threshold`.
    """
    if body.hiring_label not in ("Hired", "Rejected"):
        raise HTTPException(
            status_code=400, detail="hiring_label must be 'Hired' or 'Rejected'"
        )

    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.job_id == job_id)
    )
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.status != "pending_decision":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Resume status is '{resume.status}', expected 'pending_decision'. "
                "Decisions can only be recorded on resumes scored via /candidates/score."
            ),
        )

    resume.hiring_label = body.hiring_label
    resume.status = "decided"
    resume.decision_made_at = datetime.datetime.utcnow()
    resume.dataset_split = None  # next train picks it up via incremental split

    # Update the latest live prediction for this resume.
    pred_result = await db.execute(
        select(CandidatePrediction)
        .where(CandidatePrediction.resume_id == resume_id)
        .order_by(CandidatePrediction.id.desc())
    )
    latest_pred = pred_result.scalars().first()
    if latest_pred is not None:
        latest_pred.actual_label = body.hiring_label
        latest_pred.is_correct = latest_pred.prediction == body.hiring_label

    await db.flush()

    decisions_since = await _decisions_since_last_train(db, job)
    auto_trigger = False
    if (
        decisions_since >= job.auto_retrain_threshold
        and get_run_status(job_id).get("status") != "running"
    ):
        active = await load_active_candidate(db, job_id)
        if active is not None:
            _, candidate = active
            prompts = [candidate[f"prompt_{i + 1}"] for i in range(5)]
            background_tasks.add_task(
                run_optimization_in_background,
                job_id=job_id,
                prompts=prompts,
                max_metric_calls=None,
                hire_threshold=None,
                early_stop_patience=None,
                force_resplit=False,
            )
            auto_trigger = True

    return DecisionResponse(
        resume_id=resume_id,
        hiring_label=body.hiring_label,
        decisions_since_last_train=decisions_since,
        auto_retrain_threshold=job.auto_retrain_threshold,
        auto_retrain_triggered=auto_trigger,
    )


@router.get(
    "/candidates/pending", response_model=list[PendingCandidateResponse]
)
async def list_pending_candidates(job_id: int, db: AsyncSession = Depends(get_db)):
    """List candidates scored via /candidates/score but not yet decided."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    pending_result = await db.execute(
        select(Resume)
        .where(Resume.job_id == job_id, Resume.status == "pending_decision")
        .order_by(Resume.id.desc())
    )
    pending = list(pending_result.scalars().all())
    if not pending:
        return []

    pred_result = await db.execute(
        select(CandidatePrediction)
        .where(CandidatePrediction.resume_id.in_([r.id for r in pending]))
        .order_by(CandidatePrediction.id.desc())
    )
    latest_pred_by_resume: dict[int, CandidatePrediction] = {}
    for p in pred_result.scalars().all():
        latest_pred_by_resume.setdefault(p.resume_id, p)

    return [
        PendingCandidateResponse(
            resume_id=r.id,
            candidate_name=r.candidate_name,
            file_type=r.file_type,
            aggregate_score=latest_pred_by_resume.get(r.id).aggregate_score
            if latest_pred_by_resume.get(r.id)
            else None,
            prediction=latest_pred_by_resume.get(r.id).prediction
            if latest_pred_by_resume.get(r.id)
            else None,
            candidate_set_id_used=latest_pred_by_resume.get(r.id).candidate_set_id
            if latest_pred_by_resume.get(r.id)
            else None,
            scored_at=None,
        )
        for r in pending
    ]


@router.get("/training-status", response_model=TrainingStatusResponse)
async def training_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """Lightweight summary the dashboard polls for the live-loop badge."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    decisions_since = await _decisions_since_last_train(db, job)
    active_q = await db.execute(
        select(func.count(TalentLens.id)).where(
            TalentLens.job_id == job_id,
            TalentLens.generation == "evolved",
            TalentLens.is_active.is_(True),
        )
    )
    has_active = int(active_q.scalar_one()) == 5

    return TrainingStatusResponse(
        decisions_since_last_train=decisions_since,
        auto_retrain_threshold=job.auto_retrain_threshold,
        last_optimized_at=job.last_optimized_at,
        has_active_best_prompts=has_active,
        run_status=get_run_status(job_id).get("status", "idle"),
    )


@router.post("/resumes/batch", response_model=BatchResumesUploadResponse, status_code=201)
async def batch_upload_resumes(
    job_id: int,
    body: BatchResumesUploadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Batch upload multiple resumes with predetermined hiring decisions.

    Each resume is provided as base64-encoded content. After successful upload,
    optionally triggers a warm-started retraining if auto_retrain=True.
    """
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = []
    successful = 0
    failed = 0
    settings = get_settings()

    for item in body.resumes:
        try:
            if item.hiring_label not in ("Hired", "Rejected"):
                raise ValueError("hiring_label must be 'Hired' or 'Rejected'")

            # Get file suffix from filename
            if "." not in item.file_name:
                raise ValueError("File must have an extension")
            suffix = item.file_name.rsplit(".", 1)[-1].lower()
            if suffix not in ("pdf", "docx", "txt"):
                raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")

            # Decode base64 content
            try:
                file_bytes = base64.b64decode(item.file_content_base64)
            except Exception as e:
                raise ValueError(f"Invalid base64 encoding: {e}")

            # Write file to disk
            file_id = uuid.uuid4().hex[:12]
            file_name = f"{file_id}_{item.file_name}"
            file_path = settings.upload_path / file_name
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            # Parse resume
            try:
                parsed_text = parse_resume(file_path)
            except Exception as e:
                file_path.unlink(missing_ok=True)
                raise ValueError(f"Failed to parse resume: {e}")

            # Create resume record
            resume = Resume(
                job_id=job_id,
                candidate_name=item.candidate_name,
                file_path=str(file_path),
                file_type=suffix,
                parsed_text=parsed_text,
                hiring_label=item.hiring_label,
                status="decided",
                entry_source="historical",
                decision_made_at=datetime.datetime.utcnow(),
            )
            db.add(resume)
            await db.flush()
            await db.refresh(resume)

            results.append(
                BatchResumeUploadResult(
                    candidate_name=item.candidate_name,
                    resume_id=resume.id,
                    status="success",
                    error_message=None,
                )
            )
            successful += 1

        except Exception as e:
            failed += 1
            results.append(
                BatchResumeUploadResult(
                    candidate_name=item.candidate_name,
                    resume_id=0,
                    status="error",
                    error_message=str(e),
                )
            )

    await db.commit()

    # Auto-trigger retrain if requested and successful
    auto_trigger = False
    if body.auto_retrain and successful > 0:
        try:
            decisions_since = await _decisions_since_last_train(db, job)
            if (
                decisions_since >= job.auto_retrain_threshold
                and get_run_status(job_id).get("status") != "running"
            ):
                active = await load_active_candidate(db, job_id)
                if active is not None:
                    _, candidate = active
                    prompts = [candidate[f"prompt_{i + 1}"] for i in range(5)]
                    background_tasks.add_task(
                        run_optimization_in_background,
                        job_id=job_id,
                        prompts=prompts,
                        max_metric_calls=None,
                        hire_threshold=None,
                        early_stop_patience=None,
                        force_resplit=False,
                    )
                    auto_trigger = True
        except Exception as e:
            # Log error but don't fail the response - batch upload succeeded
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Auto-retrain trigger failed: {e}", exc_info=True)

    return BatchResumesUploadResponse(
        total=len(body.resumes),
        successful=successful,
        failed=failed,
        results=results,
        auto_retrain_triggered=auto_trigger,
    )
