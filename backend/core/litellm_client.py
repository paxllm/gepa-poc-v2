"""
Rate-limited LiteLLM client for NVIDIA NIM.

Provides a global RPM throttle and retry-with-backoff on 429 / rate limits and timeouts.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Any

import litellm
from litellm.exceptions import RateLimitError, Timeout

from backend.core.config import get_settings
from backend.core import usage_tracker

_lock = threading.Lock()
_request_timestamps: list[float] = []


def get_llm_timeout() -> int:
    """Return configured per-request LLM timeout in seconds."""
    return get_settings().llm_timeout_seconds


def _is_rate_limit_error(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "too many requests" in msg


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, Timeout):
        return True
    name = type(exc).__name__.lower()
    if "timeout" in name:
        return True
    msg = str(exc).lower()
    return "timed out" in msg or "timeout" in msg


def _is_retriable_error(exc: BaseException) -> bool:
    return _is_rate_limit_error(exc) or _is_timeout_error(exc)


def _prune_old_timestamps(now: float, window_seconds: float) -> None:
    global _request_timestamps
    cutoff = now - window_seconds
    _request_timestamps = [t for t in _request_timestamps if t > cutoff]


def _acquire_rpm_slot() -> None:
    """Block until a request slot is available under the configured RPM cap."""
    settings = get_settings()
    max_rpm = settings.llm_max_rpm
    if max_rpm <= 0:
        return

    window_seconds = 60.0
    min_interval = window_seconds / max_rpm

    while True:
        with _lock:
            now = time.monotonic()
            _prune_old_timestamps(now, window_seconds)
            if len(_request_timestamps) < max_rpm:
                _request_timestamps.append(now)
                return
            oldest = _request_timestamps[0]
            wait = (oldest + window_seconds) - now
        if wait > 0:
            time.sleep(wait + random.uniform(0.01, 0.05))
        else:
            time.sleep(min_interval)


def _record_response_usage(model: str, response: Any) -> None:
    try:
        u = getattr(response, "usage", None)
        if u is None:
            return
        pt = getattr(u, "prompt_tokens", 0) or 0
        ct = getattr(u, "completion_tokens", 0) or 0
        if pt > 0 or ct > 0:
            usage_tracker.record_usage(model, pt, ct)
    except Exception:
        pass


def configure_litellm() -> str:
    """Configure litellm for NVIDIA NIM and return the task_lm model string."""
    import os

    settings = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", settings.nvidia_api_key)
    litellm.api_base = settings.nvidia_base_url
    return f"openai/{settings.nvidia_model}"


def completion_with_retry(
    *,
    model: str,
    messages: list[dict[str, str]],
    timeout: int | float | None = None,
    **kwargs: Any,
) -> Any:
    """
    Call litellm.completion with RPM throttling and exponential backoff on 429/timeouts.
    """
    settings = get_settings()
    max_retries = settings.llm_retry_max
    if timeout is None:
        timeout = get_llm_timeout()
    last_exc: BaseException | None = None

    for attempt in range(max_retries):
        _acquire_rpm_slot()
        try:
            call_kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                **kwargs,
            }
            if timeout is not None:
                call_kwargs["timeout"] = timeout
            response = litellm.completion(**call_kwargs)
            _record_response_usage(model, response)
            return response
        except Exception as exc:
            last_exc = exc
            if not _is_retriable_error(exc) or attempt >= max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0.1, 0.5)
            time.sleep(wait)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("completion_with_retry failed without an exception")


def make_reflection_lm(
    model: str,
    *,
    timeout: int | float | None = None,
    job_id: int | None = None,
    run_set_id: str | None = None,
):
    """Build a GEPA-compatible reflection_lm callable using the shared wrapper."""
    if timeout is None:
        timeout = get_llm_timeout()

    def _reflection_lm(prompt: str | list[dict[str, str]]) -> str:
        usage_tracker.set_call_context(job_id, run_set_id, "reflection")
        if isinstance(prompt, str):
            messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        else:
            messages = prompt
        completion = completion_with_retry(
            model=model,
            messages=messages,
            timeout=timeout,
        )
        return completion.choices[0].message.content or ""

    return _reflection_lm
