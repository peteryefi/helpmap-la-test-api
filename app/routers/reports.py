"""POST /reports and GET /reports -- the two endpoints for Data Flow 1."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import desc
from sqlalchemy.orm import Session
import secrets

from app.config import get_settings
from app.database import get_db
from app.models import Report
from app.ratelimit import limiter
from app.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()

def verify_admin_token(x_admin_token: Optional[str] = Header(default=None)) -> None:
    """Dependency gating DELETE /reports/{id}.

    Fails closed: if ADMIN_DELETE_TOKEN isn't set on the server, every
    delete request is rejected with 503 rather than treating an unset
    secret as "no check needed". Uses secrets.compare_digest rather than
    `==` so the comparison doesn't leak timing information about how many
    leading characters matched.
    """
    if not settings.ADMIN_DELETE_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Delete is not enabled on this server (ADMIN_DELETE_TOKEN is not set).",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_DELETE_TOKEN):
        raise HTTPException(status_code=401, detail="Missing or invalid X-Admin-Token header.")

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

@router.delete("/{report_id}", status_code=204)
@limiter.limit(settings.RATE_LIMIT_DELETE)
def delete_report(
    request: Request,
    report_id: str,
    db: Session = Depends(get_db),
    _admin: None = Depends(verify_admin_token),
):
    """Delete a single report by id. Requires a valid X-Admin-Token header.

    Returns 204 on success (matches REST convention for DELETE -- no body),
    404 if the id doesn't exist. Deletes are permanent; there's no soft-
    delete/undo for this testbed.
    """
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report with id '{report_id}' not found.")
    db.delete(report)
    db.commit()
