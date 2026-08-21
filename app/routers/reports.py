"""POST /reports and GET /reports -- the two endpoints for Data Flow 1."""
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Report
from app.ratelimit import limiter
from app.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()


@router.post("", response_model=ReportOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_SUBMIT)
def submit_report(request: Request, payload: ReportCreate, db: Session = Depends(get_db)):
    """Accept a report from the PWA and persist it so every user sees it."""
    if payload.id is not None and db.get(Report, payload.id) is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Report with id '{payload.id}' already exists.",
        )

    report = Report(**payload.model_dump(exclude_none=True))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=List[ReportOut])
@limiter.limit(settings.RATE_LIMIT_LIST)
def list_reports(request: Request, limit: int = 500, db: Session = Depends(get_db)):
    """Return recent reports, newest first, so a refreshed browser sees everyone's data.

    Only reports created within the last REPORT_WINDOW_HOURS (config.py,
    default 24h) are returned.
    """
    limit = max(1, min(limit, 500))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.REPORT_WINDOW_HOURS)
    return (
        db.query(Report)
        .filter(Report.createdAt >= cutoff)
        .order_by(desc(Report.createdAt))
        .limit(limit)
        .all()
    )
