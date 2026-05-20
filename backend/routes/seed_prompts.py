"""
Seed prompt endpoints for wizard defaults.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.constants.default_prompts import SEED_AUTHORED_SET_ID
from backend.core.database import get_db
from backend.gepa_integration.prompt_templates import normalize_prompts
from backend.models.db_models import Job, TalentLens
from backend.models.schemas import PromptSetInput, SeedPromptResponse

router = APIRouter(prefix="/api/jobs/{job_id}/seed-prompts", tags=["seed_prompts"])


@router.get("", response_model=list[SeedPromptResponse])
async def list_seed_prompts(job_id: int, db: AsyncSession = Depends(get_db)):
    """Return the 5 human-authored seed prompts for the setup wizard."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(
        select(TalentLens)
        .where(
            TalentLens.job_id == job_id,
            TalentLens.candidate_set_id == SEED_AUTHORED_SET_ID,
            TalentLens.generation == "seed",
        )
        .order_by(TalentLens.prompt_index)
    )
    lenses = result.scalars().all()

    return [
        SeedPromptResponse(prompt_index=lens.prompt_index, prompt_text=lens.prompt_text)
        for lens in lenses
    ]


@router.put("", response_model=list[SeedPromptResponse])
async def update_seed_prompts(
    job_id: int,
    request: PromptSetInput,
    db: AsyncSession = Depends(get_db),
):
    """Persist the 5 human-authored evaluation angles for the setup wizard."""
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    normalized = normalize_prompts([p.prompt_text for p in request.prompts])
    if len(normalized) != 5:
        raise HTTPException(status_code=400, detail="Exactly 5 prompts are required")

    result = await db.execute(
        select(TalentLens).where(
            TalentLens.job_id == job_id,
            TalentLens.candidate_set_id == SEED_AUTHORED_SET_ID,
            TalentLens.generation == "seed",
        )
    )
    existing = {lens.prompt_index: lens for lens in result.scalars().all()}

    for idx, prompt_text in enumerate(normalized, start=1):
        lens = existing.get(idx)
        if lens is not None:
            lens.prompt_text = prompt_text
        else:
            db.add(
                TalentLens(
                    job_id=job_id,
                    candidate_set_id=SEED_AUTHORED_SET_ID,
                    prompt_index=idx,
                    prompt_text=prompt_text,
                    iteration=0,
                    generation="seed",
                    is_active=False,
                )
            )

    await db.commit()

    updated = await db.execute(
        select(TalentLens)
        .where(
            TalentLens.job_id == job_id,
            TalentLens.candidate_set_id == SEED_AUTHORED_SET_ID,
            TalentLens.generation == "seed",
        )
        .order_by(TalentLens.prompt_index)
    )
    lenses = updated.scalars().all()

    return [
        SeedPromptResponse(prompt_index=lens.prompt_index, prompt_text=lens.prompt_text)
        for lens in lenses
    ]
