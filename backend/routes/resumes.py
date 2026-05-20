"""
Resume upload and listing endpoints.
"""

import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.models.db_models import Job, Resume
from backend.models.schemas import ResumeResponse
from backend.parser.resume_parser import parse_resume

router = APIRouter(prefix="/api/jobs/{job_id}/resumes", tags=["resumes"])


@router.post("", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    job_id: int,
    file: UploadFile = File(...),
    candidate_name: str = Form(...),
    hiring_label: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume file with its hiring label.

    Args:
        job_id: The job this resume belongs to.
        file: Resume file (PDF, DOCX, or TXT).
        candidate_name: Name of the candidate.
        hiring_label: "Hired" or "Rejected".
    """
    # Validate job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    # Validate hiring label
    if hiring_label not in ("Hired", "Rejected"):
        raise HTTPException(
            status_code=400,
            detail="hiring_label must be 'Hired' or 'Rejected'"
        )

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")

    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ("pdf", "docx", "txt"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use PDF, DOCX, or TXT."
        )

    # Save file
    settings = get_settings()
    file_id = uuid.uuid4().hex[:12]
    file_name = f"{file_id}_{file.filename}"
    file_path = settings.upload_path / file_name

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse resume text
    try:
        parsed_text = parse_resume(file_path)
    except Exception as e:
        # Clean up file on parse failure
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {e}")

    # Store in database
    resume = Resume(
        job_id=job_id,
        candidate_name=candidate_name,
        file_path=str(file_path),
        file_type=suffix,
        parsed_text=parsed_text,
        hiring_label=hiring_label,
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(job_id: int, db: AsyncSession = Depends(get_db)):
    """List all resumes for a job."""
    result = await db.execute(
        select(Resume).where(Resume.job_id == job_id)
    )
    return result.scalars().all()


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(job_id: int, resume_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific resume with its parsed text."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.job_id == job_id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
