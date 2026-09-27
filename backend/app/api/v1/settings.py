"""Settings routes: AI provider status."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import AuthContext, get_current_user, settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/ai-provider")
def get_ai_provider(auth: AuthContext = Depends(get_current_user)) -> dict[str, object]:
    provider = settings.AI_PROVIDER
    configured = True
    if provider == "azure_openai":
        configured = bool(
            settings.AZURE_OPENAI_ENDPOINT
            and settings.AZURE_OPENAI_API_KEY
            and settings.AZURE_OPENAI_DEPLOYMENT
        )
    return {
        "provider": provider,
        "configured": configured,
        "demo_mode": provider == "demo",
    }
