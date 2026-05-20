"""
Core values CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.db_models import CoreValue, Job
from backend.models.schemas import CoreValueBatchCreate, CoreValueResponse

router = APIRouter(prefix="/api/jobs/{job_id}/core-values", tags=["core_values"])


@router.post("", response_model=list[CoreValueResponse], status_code=201)
async def create_core_values(
    job_id: int,
    batch: CoreValueBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add core values to a job (batch create)."""
    # Verify job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    created = []
    for cv_data in batch.core_values:
        cv = CoreValue(
            job_id=job_id,
            name=cv_data.name,
            description=cv_data.description,
        )
        db.add(cv)
        created.append(cv)

    await db.flush()
    for cv in created:
        await db.refresh(cv)

    return created


@router.get("", response_model=list[CoreValueResponse])
async def list_core_values(job_id: int, db: AsyncSession = Depends(get_db)):
    """List all core values for a job."""
    result = await db.execute(
        select(CoreValue).where(CoreValue.job_id == job_id)
    )
    return result.scalars().all()
