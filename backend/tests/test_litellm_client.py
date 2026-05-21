"""Tests for rate-limited LiteLLM client."""

from unittest.mock import MagicMock, patch

import pytest
from litellm.exceptions import RateLimitError, Timeout

from backend.core import litellm_client


@pytest.fixture(autouse=True)
def reset_rpm_state():
    litellm_client._request_timestamps.clear()
    yield
    litellm_client._request_timestamps.clear()


@patch("backend.core.litellm_client.litellm.completion")
def test_completion_with_retry_succeeds(mock_completion):
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="ok"))]
    )
    result = litellm_client.completion_with_retry(
        model="openai/test",
        messages=[{"role": "user", "content": "hi"}],
        timeout=30,
    )
    assert result.choices[0].message.content == "ok"
    mock_completion.assert_called_once()


@patch("backend.core.litellm_client.time.sleep")
@patch("backend.core.litellm_client.litellm.completion")
def test_completion_with_retry_retries_on_timeout(mock_completion, mock_sleep):
    mock_completion.side_effect = [
        Timeout("timed out", model="test", llm_provider="openai"),
        MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
    ]
    result = litellm_client.completion_with_retry(
        model="openai/test",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.choices[0].message.content == "ok"
    assert mock_completion.call_count == 2
    mock_sleep.assert_called_once()


@patch("backend.core.litellm_client.time.sleep")
@patch("backend.core.litellm_client.litellm.completion")
def test_completion_with_retry_retries_on_429(mock_completion, mock_sleep):
    mock_completion.side_effect = [
        RateLimitError("429", llm_provider="openai", model="test"),
        MagicMock(choices=[MagicMock(message=MagicMock(content="ok"))]),
    ]
    result = litellm_client.completion_with_retry(
        model="openai/test",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.choices[0].message.content == "ok"
    assert mock_completion.call_count == 2
    mock_sleep.assert_called_once()


def test_make_reflection_lm_string_prompt():
    with patch(
        "backend.core.litellm_client.completion_with_retry",
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="reflection"))]
        ),
    ) as mock_completion:
        fn = litellm_client.make_reflection_lm("openai/test")
        assert fn("reflect on this") == "reflection"
        mock_completion.assert_called_once_with(
            model="openai/test",
            messages=[{"role": "user", "content": "reflect on this"}],
            timeout=300,
        )
