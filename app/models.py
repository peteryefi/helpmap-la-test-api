"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text

from app.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=_new_id)
    description = Column(String, nullable=False)
    # Base64-encoded image data for this testbed (not a hosted URL, despite
    # the name -- kept as `photoUrl` to match the frontend's field name
    # exactly).
    photoUrl = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    createdAt = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    type = Column(String, nullable=False)
