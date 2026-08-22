"""Minimal smoke tests. Run with: pytest

Uses its own SQLite file (separate from the app's default data/reports.db)
so running tests never touches real demo data.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_reports.db")
os.environ.setdefault("ADMIN_DELETE_TOKEN", "test-admin-token-do-not-use-in-prod")

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

settings = get_settings()


@pytest.fixture(scope="module")
def client():
    # Entering TestClient as a context manager triggers FastAPI's lifespan
    # (startup/shutdown) events -- without this, init_db() never runs and
    # the `reports` table doesn't exist yet when tests hit the DB.
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_submit_and_list_report(client):
    payload = {
        "description": "Fire in the park.",
        "latitude": 34.090599,
        "longitude": -118.2468,
        "type": "Fire",
    }
    submit = client.post("/reports", json=payload)
    assert submit.status_code == 201
    created = submit.json()
    assert created["description"] == payload["description"]
    assert created["id"]  # server-generated UUID since none was sent

    listing = client.get("/reports")
    assert listing.status_code == 200
    ids = [r["id"] for r in listing.json()]
    assert created["id"] in ids


def test_client_supplied_id_is_honored(client):
    payload = {
        "id": "mock-1",
        "description": "Fire in the park.",
        "photoUrl": "https://example.com/fire.jpg",
        "latitude": 34.090599,
        "longitude": -118.2468,
        "createdAt": "2026-08-11T17:00:00.000Z",
        "type": "Fire",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == "mock-1"
    assert body["photoUrl"] == payload["photoUrl"]


def test_duplicate_client_id_rejected(client):
    payload = {
        "id": "mock-dup-test",
        "description": "Fire in the park.",
        "latitude": 34.090599,
        "longitude": -118.2468,
        "type": "Fire",
    }
    first = client.post("/reports", json=payload)
    assert first.status_code == 201
    second = client.post("/reports", json=payload)
    assert second.status_code == 409


def test_invalid_coordinates_rejected(client):
    payload = {
        "description": "Bad coords",
        "latitude": 999,
        "longitude": -118.2468,
        "type": "Fire",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 422


def test_base64_photo_round_trips(client):
    fake_photo = "data:image/jpeg;base64," + ("QQ==" * 500)  # ~2KB base64
    payload = {
        "id": "photo-test-1",
        "description": "Smoke visible near the trail",
        "photoUrl": fake_photo,
        "latitude": 34.09,
        "longitude": -118.25,
        "type": "Fire",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 201
    assert resp.json()["photoUrl"] == fake_photo

    listing = client.get("/reports")
    match = next(r for r in listing.json() if r["id"] == "photo-test-1")
    assert match["photoUrl"] == fake_photo


def test_oversized_photo_rejected(client):
    too_big = "A" * (settings.MAX_PHOTO_BASE64_CHARS + 1)
    payload = {
        "description": "Photo too large",
        "photoUrl": too_big,
        "latitude": 34.09,
        "longitude": -118.25,
        "type": "Fire",
    }
    resp = client.post("/reports", json=payload)
    assert resp.status_code == 422


def test_report_outside_window_is_excluded(client):
    old_time = datetime.now(timezone.utc) - timedelta(hours=settings.REPORT_WINDOW_HOURS + 1)
    payload = {
        "id": "window-test-old",
        "description": "Old report, should be filtered out",
        "latitude": 34.09,
        "longitude": -118.25,
        "createdAt": old_time.isoformat(),
        "type": "Fire",
    }
    submit = client.post("/reports", json=payload)
    assert submit.status_code == 201  # stored, just not listed

    listing = client.get("/reports")
    ids = [r["id"] for r in listing.json()]
    assert "window-test-old" not in ids


def test_report_inside_window_is_included(client):
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    payload = {
        "id": "window-test-recent",
        "description": "Recent report, should be listed",
        "latitude": 34.09,
        "longitude": -118.25,
        "createdAt": recent_time.isoformat(),
        "type": "Fire",
    }
    submit = client.post("/reports", json=payload)
    assert submit.status_code == 201

    listing = client.get("/reports")
    ids = [r["id"] for r in listing.json()]
    assert "window-test-recent" in ids

def test_delete_without_token_rejected(client):
    payload = {
        "id": "delete-test-no-token",
        "description": "Should survive this request",
        "latitude": 34.09,
        "longitude": -118.25,
        "type": "Fire",
    }
    client.post("/reports", json=payload)

    resp = client.delete("/reports/delete-test-no-token")
    assert resp.status_code == 401

    # confirm it wasn't actually deleted
    listing = client.get("/reports")
    ids = [r["id"] for r in listing.json()]
    assert "delete-test-no-token" in ids

def test_delete_with_wrong_token_rejected(client):
    payload = {
        "id": "delete-test-wrong-token",
        "description": "Should survive this request too",
        "latitude": 34.09,
        "longitude": -118.25,
        "type": "Fire",
    }
    client.post("/reports", json=payload)

    resp = client.delete(
        "/reports/delete-test-wrong-token",
        headers={"X-Admin-Token": "not-the-real-token"},
    )
    assert resp.status_code == 401

    listing = client.get("/reports")
    ids = [r["id"] for r in listing.json()]
    assert "delete-test-wrong-token" in ids

def test_delete_with_correct_token_succeeds(client):
    payload = {
        "id": "delete-test-success",
        "description": "Should actually be deleted",
        "latitude": 34.09,
        "longitude": -118.25,
        "type": "Fire",
    }
    client.post("/reports", json=payload)

    resp = client.delete(
        "/reports/delete-test-success",
        headers={"X-Admin-Token": os.environ["ADMIN_DELETE_TOKEN"]},
    )
    assert resp.status_code == 204

    listing = client.get("/reports")
    ids = [r["id"] for r in listing.json()]
    assert "delete-test-success" not in ids

def test_delete_nonexistent_id_returns_404(client):
    resp = client.delete(
        "/reports/this-id-does-not-exist",
        headers={"X-Admin-Token": os.environ["ADMIN_DELETE_TOKEN"]},
    )
    assert resp.status_code == 404