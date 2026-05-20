"""
LLM client for NVIDIA NIM API.

Delegates to the rate-limited LiteLLM wrapper used by GEPA optimization.
"""

import json
from typing import Any

from backend.core.config import get_settings
from backend.core.litellm_client import completion_with_retry, configure_litellm


def get_task_lm_model() -> str:
    """Return configured LiteLLM model id and ensure NVIDIA NIM env is set."""
    return configure_litellm()


def llm_chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: dict | None = None,
    max_retries: int | None = None,
) -> str:
    """
    Send a chat completion request to NVIDIA NIM with rate limiting and retries.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        model: Model identifier. Defaults to settings.nvidia_model via configure_litellm().
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.
        response_format: Optional response format (e.g., {"type": "json_object"}).
        max_retries: Ignored; retries are controlled by settings.llm_retry_max.

    Returns:
        The assistant's response text.
    """
    _ = max_retries
    settings = get_settings()
    configure_litellm()
    if model and "/" in model:
        task_model = model
    elif model:
        task_model = f"openai/{model}"
    else:
        task_model = f"openai/{settings.nvidia_model}"

    kwargs: dict[str, Any] = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    completion = completion_with_retry(
        model=task_model,
        messages=messages,
        **kwargs,
    )
    return completion.choices[0].message.content or ""


def llm_json_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> dict:
    """
    Send a chat completion request and parse JSON response.
    Falls back to extracting JSON from markdown code blocks if needed.
    """
    response_text = llm_chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        if "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        raise
