"""Unit tests for the OpenAI provider (mocked httpx, no network)."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.openai import API_URL, OpenAIProvider
from app.providers.schemas import GenerationRequest, StructuredGenerationResult
from app.core.config import Settings
from app.services.generation_service import get_provider

API_KEY = "sk-test-key-not-a-real-secret"
MODEL = "gpt-4o-mini"


def _valid_payload() -> dict:
    return {
        "summary": "Static website on Azure Blob Storage.",
        "assumptions": ["Single region is acceptable."],
        "architecture": {
            "overview": "Blob static website behind CDN.",
            "components": [
                {"name": "storage", "purpose": "Hosts static assets."}
            ],
            "traffic_flow": ["user -> cdn -> storage"],
        },
        "assets": [
            {
                "asset_type": "terraform",
                "file_name": "main.tf",
                "language": "hcl",
                "content": 'resource "azurerm_storage_account" "web" {}',
            }
        ],
        "security_findings": [
            {
                "severity": "medium",
                "title": "Public blob access",
                "description": "Container allows public read.",
                "recommendation": "Restrict to CDN origin.",
            }
        ],
        "zero_trust": {
            "identity_score": 80,
            "network_score": 70,
            "data_score": 75,
            "workload_score": 70,
            "overall_score": 74,
            "recommendations": ["Enable managed identity."],
        },
        "cost_guidance": {
            "disclaimer": "Estimates only.",
            "cost_drivers": ["Storage transactions."],
            "optimization_recommendations": ["Use cool tier for archives."],
        },
    }


def _request() -> GenerationRequest:
    return GenerationRequest(project_name="web", original_prompt="a static site")


class _FakeResponse:
    def __init__(self, status_code: int, payload: object = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload


def _ok_response() -> _FakeResponse:
    return _FakeResponse(
        200,
        {"choices": [{"message": {"content": json.dumps(_valid_payload())}}]},
    )


def test_success_returns_validated_result() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    with patch("httpx.post", return_value=_ok_response()) as mock_post:
        result = provider.generate(_request())
    assert isinstance(result, StructuredGenerationResult)
    assert result.summary == "Static website on Azure Blob Storage."
    assert result.assets[0].asset_type == "terraform"
    # Request shape: OpenAI URL, Bearer auth, model in payload.
    args, kwargs = mock_post.call_args
    assert args[0] == API_URL
    assert kwargs["headers"]["Authorization"] == f"Bearer {API_KEY}"
    assert kwargs["json"]["model"] == MODEL
    assert kwargs["json"]["response_format"] == {"type": "json_object"}
    assert kwargs["timeout"] == 90.0


def test_timeout_raises_provider_error() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    with patch(
        "httpx.post", side_effect=httpx.TimeoutException("timed out")
    ), pytest.raises(ProviderError, match="timed out"):
        provider.generate(_request())


def test_http_429_is_retryable() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    with patch("httpx.post", return_value=_FakeResponse(429)), pytest.raises(
        ProviderError
    ) as exc_info:
        provider.generate(_request())
    assert exc_info.value.retryable is True
    assert "429" in str(exc_info.value)


def test_http_400_is_not_retryable() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    with patch("httpx.post", return_value=_FakeResponse(400)), pytest.raises(
        ProviderError
    ) as exc_info:
        provider.generate(_request())
    assert exc_info.value.retryable is False


def test_invalid_json_raises_provider_error() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    bad = _FakeResponse(
        200, {"choices": [{"message": {"content": "not json at all"}}]}
    )
    with patch("httpx.post", return_value=bad), pytest.raises(
        ProviderError, match="unreadable"
    ):
        provider.generate(_request())


def test_schema_invalid_json_raises_provider_error() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    bad = _FakeResponse(
        200, {"choices": [{"message": {"content": json.dumps({"nope": 1})}}]}
    )
    with patch("httpx.post", return_value=bad), pytest.raises(
        ProviderError, match="schema validation"
    ):
        provider.generate(_request())


def test_missing_api_key_raises_on_construction() -> None:
    with pytest.raises(ProviderError, match="not configured"):
        OpenAIProvider(api_key="", model=MODEL)


def test_api_key_never_leaks_into_errors() -> None:
    provider = OpenAIProvider(api_key=API_KEY, model=MODEL)
    with patch(
        "httpx.post",
        side_effect=httpx.HTTPError(f"connection failed, api_key={API_KEY}"),
    ), pytest.raises(ProviderError) as exc_info:
        provider.generate(_request())
    assert API_KEY not in str(exc_info.value)


def test_get_provider_wires_openai_settings() -> None:
    settings = Settings(AI_PROVIDER="openai", OPENAI_API_KEY=API_KEY)
    provider = get_provider(settings)
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openai"
    assert provider.model == "gpt-4o-mini"
