"""Azure OpenAI provider: REST via httpx, JSON-mode chat completions.

Timeout 90s. Errors are sanitized (no credentials or raw response bodies leak
into error messages). The raw model output is validated against the Pydantic
contract; invalid output is rejected with a sanitized error so the caller can
retry.
"""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from app.core.security import sanitize_error_message
from app.providers.base import AIProvider, ProviderError
from app.providers.schemas import (
    SYSTEM_PROMPT,
    GenerationRequest,
    StructuredGenerationResult,
)

TIMEOUT_SECONDS = 90.0


class AzureOpenAIProvider(AIProvider):
    name = "azure_openai"
    model: str

    def __init__(
        self, endpoint: str, api_key: str, deployment: str, api_version: str
    ) -> None:
        if not endpoint or not api_key or not deployment:
            raise ProviderError(
                "Azure OpenAI is not configured (endpoint/key/deployment)."
            )
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        self.model = deployment

    def generate(self, request: GenerationRequest) -> StructuredGenerationResult:
        url = (
            f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions"
            f"?api-version={self.api_version}"
        )
        user_content = self._user_message(request)
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        try:
            response = httpx.post(
                url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS
            )
        except httpx.TimeoutException as exc:
            raise ProviderError("Azure OpenAI request timed out.") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"Azure OpenAI request failed: {sanitize_error_message(str(exc))}"
            ) from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"Azure OpenAI returned HTTP {response.status_code}.",
                retryable=response.status_code in (429, 500, 502, 503, 504),
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "Azure OpenAI returned an unreadable response."
            ) from exc

        try:
            return StructuredGenerationResult.model_validate(parsed)
        except ValidationError as exc:
            raise ProviderError(
                "Azure OpenAI output failed schema validation: "
                + sanitize_error_message(str(exc.errors()[:3]))
            ) from exc

    def _user_message(self, request: GenerationRequest) -> str:
        lines = [
            f"Project name: {request.project_name}",
            f"Cloud target: {request.cloud_target}",
            f"Environment: {request.environment}",
            f"Region: {request.region}",
            f"Availability requirement: {request.availability_requirement}",
            f"Compliance framework: {request.compliance_framework}",
        ]
        if request.description:
            lines.append(f"Description: {request.description}")
        detail = request.prompt_override or request.original_prompt
        if detail:
            lines.append(f"User request: {detail}")
        lines.append("Emit all 16 asset types defined in the schema.")
        return "\n".join(lines)
