"""AI provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.providers.schemas import GenerationRequest, StructuredGenerationResult


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, request: GenerationRequest) -> StructuredGenerationResult:
        """Run a generation and return validated structured output.

        Raises ProviderError on any failure.
        """
        raise NotImplementedError


class ProviderError(Exception):
    """Raised when a provider fails (network, auth, invalid output, ...)."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable
