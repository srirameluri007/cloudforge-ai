"""Asset schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    generation_id: str
    asset_type: str
    file_name: str
    language: str
    content: str
    content_hash: str
    created_at: datetime


class AssetSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_type: str
    file_name: str
    language: str
    content_hash: str
    created_at: datetime


class AssetList(BaseModel):
    items: list[AssetSummaryOut]
