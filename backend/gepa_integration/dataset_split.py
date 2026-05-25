"""
Stratified train / val / test assignment for resumes (hold-out evaluation).
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.models.db_models import Resume


def _global_split_counts(n: int, train_ratio: float, val_ratio: float, test_ratio: float) -> tuple[int, int, int]:
    """Integer counts that sum to n, each split at least 1 when possible."""
    n_train = max(1, round(n * train_ratio))
    n_val = max(1, round(n * val_ratio))
    n_test = n - n_train - n_val
    while n_test < 1 and n_train > 1:
        n_train -= 1
        n_test = n - n_train - n_val
    while n_test < 1 and n_val > 1:
        n_val -= 1
        n_test = n - n_train - n_val
    if n_train + n_val + n_test != n:
        n_test = n - n_train - n_val
    if n_test < 1:
        raise ValueError("Could not form a valid 3-way split for this dataset size.")
    return n_train, n_val, n_test


def _stratified_order(resumes: list[Resume], rng: random.Random) -> list[Resume]:
    """
    Merge per-label shuffled lists in round-robin order so each split gets a
    similar mix of hiring_label values.
    """
    by_label: dict[str, list[Resume]] = defaultdict(list)
    for r in resumes:
        by_label[r.hiring_label].append(r)
    labels = list(by_label.keys())
    rng.shuffle(labels)
    for lab in labels:
        rng.shuffle(by_label[lab])

    order: list[Resume] = []
    ptr = {lab: 0 for lab in labels}
    remaining = len(resumes)
    while remaining > 0:
        for lab in labels:
            if ptr[lab] < len(by_label[lab]):
                order.append(by_label[lab][ptr[lab]])
                ptr[lab] += 1
                remaining -= 1
    return order


async def assign_splits(
    session: AsyncSession,
    job_id: int,
    *,
    train_ratio: float | None = None,
    val_ratio: float | None = None,
    test_ratio: float | None = None,
    seed: int | None = None,
    force_resplit: bool = False,
) -> dict[str, Any]:
    """
    Assign dataset_split on all parsed resumes for the job.

    Reuses existing splits unless force_resplit is True or any resume has split None.

    Returns summary dict with counts per split.
    """
    settings = get_settings()
    train_ratio = train_ratio if train_ratio is not None else settings.train_split_ratio
    val_ratio = val_ratio if val_ratio is not None else settings.val_split_ratio
    test_ratio = test_ratio if test_ratio is not None else settings.test_split_ratio
    seed = seed if seed is not None else settings.gepa_seed

    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio must sum to 1.0")

    result = await session.execute(
        select(Resume).where(
            Resume.job_id == job_id,
            Resume.parsed_text.is_not(None),
            Resume.status == "decided",
            Resume.hiring_label.is_not(None),
        )
    )
    resumes = list(result.scalars().all())
    n = len(resumes)
    min_n = settings.min_resumes_for_split
    if n < min_n:
        raise ValueError(
            f"At least {min_n} parsed resumes are required for train/val/test split (got {n})."
        )

    fully_split = bool(resumes) and all(
        r.dataset_split in ("train", "val", "test") for r in resumes
    )
    if not force_resplit and fully_split:
        counts = _split_summary(resumes)
        return {"reused": True, **counts}

    if force_resplit:
        await session.execute(
            update(Resume).where(Resume.job_id == job_id).values(dataset_split=None)
        )
        await session.flush()
        result = await session.execute(
            select(Resume).where(
                Resume.job_id == job_id,
                Resume.parsed_text.is_not(None),
                Resume.status == "decided",
                Resume.hiring_label.is_not(None),
            )
        )
        resumes = list(result.scalars().all())

    rng = random.Random(seed ^ job_id)
    unassigned = [r for r in resumes if r.dataset_split not in ("train", "val", "test")]

    if force_resplit or not any(r.dataset_split in ("train", "val", "test") for r in resumes):
        # Global re-split: stratified round-robin across all resumes.
        n_train, n_val, n_test = _global_split_counts(n, train_ratio, val_ratio, test_ratio)
        order = _stratified_order(resumes, rng)
        for i, r in enumerate(order):
            if i < n_train:
                r.dataset_split = "train"
            elif i < n_train + n_val:
                r.dataset_split = "val"
            else:
                r.dataset_split = "test"
    else:
        # Incremental: leave existing assignments alone; place new resumes
        # into whichever split is most under-target relative to the configured ratios.
        ratios = {"train": train_ratio, "val": val_ratio, "test": test_ratio}
        order = _stratified_order(unassigned, rng)
        for r in order:
            current = {
                "train": sum(1 for x in resumes if x.dataset_split == "train"),
                "val": sum(1 for x in resumes if x.dataset_split == "val"),
                "test": sum(1 for x in resumes if x.dataset_split == "test"),
            }
            total_assigned = sum(current.values()) + 1  # incl. the one we're about to place
            # Pick the split with the largest positive deficit (target - actual).
            deficits = {
                split: ratios[split] * total_assigned - current[split]
                for split in ("train", "val", "test")
            }
            choice = max(deficits, key=deficits.get)
            r.dataset_split = choice

    await session.commit()

    result2 = await session.execute(
        select(Resume).where(
            Resume.job_id == job_id,
            Resume.parsed_text.is_not(None),
            Resume.status == "decided",
            Resume.hiring_label.is_not(None),
        )
    )
    refreshed = list(result2.scalars().all())
    counts = _split_summary(refreshed)
    return {"reused": False, **counts}


def _split_summary(resumes: list[Resume]) -> dict[str, Any]:
    train_c = sum(1 for r in resumes if r.dataset_split == "train")
    val_c = sum(1 for r in resumes if r.dataset_split == "val")
    test_c = sum(1 for r in resumes if r.dataset_split == "test")
    return {
        "train": train_c,
        "val": val_c,
        "test": test_c,
        "total": len(resumes),
    }


async def clear_splits(session: AsyncSession, job_id: int) -> None:
    """Reset dataset_split for all resumes on a job (e.g. before force_resplit)."""
    await session.execute(
        update(Resume).where(Resume.job_id == job_id).values(dataset_split=None)
    )
    await session.commit()
