"""Pydantic request/response schemas.

Field names match the frontend report shape exactly (camelCase: photoUrl,
createdAt) so the PWA can consume API responses with no adapter layer.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings

settings = get_settings()


class ReportCreate(BaseModel):
    """Payload for POST /reports.
    `id` and `createdAt` are optional: the server fills in a UUID / the
    current UTC time if the client doesn't send one.
    """

    id: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=2000)
    photoUrl: Optional[str] = Field(default=None, max_length=settings.MAX_PHOTO_BASE64_CHARS)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    createdAt: Optional[datetime] = None
    type: str = Field(..., min_length=1, max_length=100)


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    description: str
    photoUrl: Optional[str] = None
    latitude: float
    longitude: float
    createdAt: datetime
    type: str
