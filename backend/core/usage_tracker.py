"""
Thread-safe LLM token usage accumulator.

Call set_call_context() at the start of any LLM-calling scope to tag
subsequent records with job_id / run_set_id / call_type. Uses threading.local
so each thread maintains independent context.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class UsageRecord:
    job_id: int | None
    run_set_id: str | None
    call_type: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


_lock = threading.Lock()
_pending: deque[UsageRecord] = deque()
_ctx = threading.local()


def set_call_context(
    job_id: int | None,
    run_set_id: str | None,
    call_type: str,
) -> None:
    """Set context for LLM calls made in the current thread."""
    _ctx.job_id = job_id
    _ctx.run_set_id = run_set_id
    _ctx.call_type = call_type


def record_usage(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Append a usage record using the current thread's context."""
    record = UsageRecord(
        job_id=getattr(_ctx, "job_id", None),
        run_set_id=getattr(_ctx, "run_set_id", None),
        call_type=getattr(_ctx, "call_type", "unknown"),
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    with _lock:
        _pending.append(record)


def drain_pending() -> list[UsageRecord]:
    """Return and clear all accumulated records."""
    with _lock:
        records = list(_pending)
        _pending.clear()
    return records


def peek_pending() -> list[UsageRecord]:
    """Return accumulated records without clearing."""
    with _lock:
        return list(_pending)
