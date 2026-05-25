"""
Shared helper: load a job's currently-serving 5-prompt candidate.

Used by the live scoring endpoint, the manual /retrain endpoint, and
the auto-retrain trigger inside the decision endpoint.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.db_models import TalentLens


async def load_active_candidate(
    db: AsyncSession, job_id: int
) -> tuple[str, dict[str, str]] | None:
    """Return (candidate_set_id, {prompt_1..prompt_5: text}) for the job.

    Prefers the active evolved best (is_active=True, generation='evolved').
    Falls back to the most-recent seed set so the system is usable right
    after the wizard, before any optimization has completed.

    Returns None if no full 5-prompt set is available.
    """
    evolved_q = await db.execute(
        select(TalentLens)
        .where(
            TalentLens.job_id == job_id,
            TalentLens.generation == "evolved",
            TalentLens.is_active.is_(True),
        )
        .order_by(TalentLens.created_at.desc(), TalentLens.prompt_index)
    )
    by_evolved: dict[str, list[TalentLens]] = defaultdict(list)
    for lens in evolved_q.scalars().all():
        by_evolved[lens.candidate_set_id].append(lens)

    # Pick the most recently-created complete set (exactly 5 prompts).
    # Iterating in insertion order (Python 3.7+) means the first complete
    # set encountered is the most recently written one (DESC sort above).
    for set_id, lenses in by_evolved.items():
        if len(lenses) == 5:
            lenses.sort(key=lambda l: l.prompt_index)
            return set_id, {
                f"prompt_{l.prompt_index}": l.prompt_text for l in lenses
            }

    seed_q = await db.execute(
        select(TalentLens)
        .where(TalentLens.job_id == job_id, TalentLens.generation == "seed")
        .order_by(TalentLens.created_at.desc(), TalentLens.prompt_index)
    )
    by_set: dict[str, list[TalentLens]] = defaultdict(list)
    for lens in seed_q.scalars().all():
        by_set[lens.candidate_set_id].append(lens)
    for set_id, lenses in by_set.items():
        if len(lenses) == 5:
            lenses.sort(key=lambda l: l.prompt_index)
            return set_id, {
                f"prompt_{l.prompt_index}": l.prompt_text for l in lenses
            }
    return None
