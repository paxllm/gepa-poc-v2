"""Tests for MetricsPersistenceCallback persistence behavior."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.gepa_integration.metrics_callback import MetricsPersistenceCallback
from backend.models.db_models import TalentLens


@pytest.mark.asyncio
async def test_persist_interim_best_replaces_prior_rows():
    stored_rows: list[TalentLens] = []
    execute_calls = 0

    async def fake_execute(_stmt):
        nonlocal execute_calls
        execute_calls += 1
        stored_rows.clear()

    session = AsyncMock()
    session.execute = fake_execute
    session.add = lambda row: stored_rows.append(row)
    session.commit = AsyncMock()

    session_ctx = AsyncMock()
    session_ctx.__aenter__.return_value = session
    session_ctx.__aexit__.return_value = None

    factory = MagicMock(return_value=session_ctx)
    loop = asyncio.get_running_loop()
    run_status: dict[int, dict] = {1: {"status": "running"}}

    callback = MetricsPersistenceCallback(
        job_id=1,
        candidate_set_id="run_abc123",
        session_factory=factory,
        loop=loop,
        run_status=run_status,
    )

    candidate_v1 = {f"prompt_{i}": f"lens v1 {i}" for i in range(1, 6)}
    candidate_v2 = {f"prompt_{i}": f"lens v2 {i}" for i in range(1, 6)}

    await callback._persist_interim_best(1, candidate_v1, 0.8)
    assert execute_calls == 1
    assert len(stored_rows) == 5
    assert stored_rows[0].prompt_text == "lens v1 1"
    assert stored_rows[0].candidate_set_id == "run_abc123_interim"

    await callback._persist_interim_best(2, candidate_v2, 0.9)
    assert execute_calls == 2
    assert len(stored_rows) == 5
    assert stored_rows[0].prompt_text == "lens v2 1"
    assert stored_rows[0].fitness_score == 0.9
