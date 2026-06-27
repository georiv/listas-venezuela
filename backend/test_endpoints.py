"""Smoke tests for the API wiring — run without real API keys.

These verify routing, validation and error handling without hitting
Google Vision, Claude or Supabase.
"""
import io
import os

# Dummy env so module-level os.environ reads don't crash on import.
os.environ.setdefault("GEMINI_API_KEY", "dummy")
os.environ.setdefault("SUPABASE_URL", "https://dummy.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "dummy")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_routes_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/upload" in paths
    assert "/records/search" in paths
    assert "/records/{record_id}" in paths


def test_upload_rejects_bad_mimetype():
    r = client.post(
        "/upload",
        files=[("files", ("lista.txt", io.BytesIO(b"hola"), "text/plain"))],
        data={"centro_hint": ""},
    )
    assert r.status_code == 415
    assert "válida" in r.json()["detail"].lower()


def test_search_requires_min_length():
    r = client.get("/records/search", params={"q": "a"})
    assert r.status_code == 422
