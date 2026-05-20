"""Tests for stratified dataset splitting."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.database import Base, migrate_schema
from backend.gepa_integration.dataset_split import assign_splits
from backend.models.db_models import Job, Resume


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await migrate_schema(conn)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        job = Job(title="Test Job", description="Test description")
        sess.add(job)
        await sess.flush()

        for i in range(30):
            label = "Hired" if i % 2 == 0 else "Rejected"
            sess.add(
                Resume(
                    job_id=job.id,
                    candidate_name=f"Candidate {i}",
                    file_path=f"/tmp/{i}.txt",
                    file_type="txt",
                    parsed_text=f"Resume text {i}",
                    hiring_label=label,
                )
            )
        await sess.commit()
        yield sess, job.id

    await engine.dispose()


@pytest.mark.asyncio
async def test_stratified_split_counts(session):
    sess, job_id = session
    summary = await assign_splits(sess, job_id, seed=42)
    assert summary["total"] == 30
    assert summary["train"] + summary["val"] + summary["test"] == 30
    assert summary["train"] >= 1
    assert summary["val"] >= 1
    assert summary["test"] >= 1


@pytest.mark.asyncio
async def test_stratified_split_label_balance(session):
    sess, job_id = session
    await assign_splits(sess, job_id, seed=42)

    from sqlalchemy import select

    result = await sess.execute(select(Resume).where(Resume.job_id == job_id))
    resumes = result.scalars().all()

    for split in ("train", "val", "test"):
        split_resumes = [r for r in resumes if r.dataset_split == split]
        hired = sum(1 for r in split_resumes if r.hiring_label == "Hired")
        rejected = len(split_resumes) - hired
        assert abs(hired - rejected) <= 1


@pytest.mark.asyncio
async def test_split_is_deterministic(session):
    sess, job_id = session
    s1 = await assign_splits(sess, job_id, seed=99, force_resplit=True)

    from sqlalchemy import select

    result = await sess.execute(select(Resume).where(Resume.job_id == job_id))
    first = {r.id: r.dataset_split for r in result.scalars().all()}

    await assign_splits(sess, job_id, seed=99, force_resplit=True)
    result = await sess.execute(select(Resume).where(Resume.job_id == job_id))
    second = {r.id: r.dataset_split for r in result.scalars().all()}

    assert first == second
    assert s1["train"] + s1["val"] + s1["test"] == 30


@pytest.mark.asyncio
async def test_reuse_existing_splits(session):
    sess, job_id = session
    await assign_splits(sess, job_id, seed=1)

    from sqlalchemy import select

    result = await sess.execute(select(Resume).where(Resume.job_id == job_id))
    before = {r.id: r.dataset_split for r in result.scalars().all()}

    summary = await assign_splits(sess, job_id, seed=999)
    assert summary["reused"] is True

    result = await sess.execute(select(Resume).where(Resume.job_id == job_id))
    after = {r.id: r.dataset_split for r in result.scalars().all()}
    assert before == after


@pytest.mark.asyncio
async def test_minimum_six_resumes():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await migrate_schema(conn)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        job = Job(title="Small", description="x")
        sess.add(job)
        await sess.flush()
        for i in range(6):
            sess.add(
                Resume(
                    job_id=job.id,
                    candidate_name=f"C{i}",
                    file_path=f"/tmp/{i}.txt",
                    file_type="txt",
                    parsed_text="text",
                    hiring_label="Hired" if i % 2 == 0 else "Rejected",
                )
            )
        await sess.commit()
        summary = await assign_splits(sess, job.id, seed=7)
        assert summary["total"] == 6
        assert summary["train"] + summary["val"] + summary["test"] == 6

    await engine.dispose()
