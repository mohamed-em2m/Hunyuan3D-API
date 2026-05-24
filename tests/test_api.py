"""
tests/test_api.py
~~~~~~~~~~~~~~~~~
Integration tests for the FastAPI endpoints using httpx TestClient.
The ModelManager is NOT initialised during these tests (hy3dgen not needed).
"""

import pytest
from fastapi.testclient import TestClient

from hunyuan3d_api.app import create_app


# Patch model loading so tests run without GPU / hy3dgen
@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_root_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "supported_formats" in data


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline_loaded" in data
    assert "cuda_available" in data


def test_generate_3d_no_file_returns_422(client):
    """POST without an image must return 422 Unprocessable Entity."""
    resp = client.post("/generate-3d")
    assert resp.status_code == 422


def test_generate_3d_unsupported_format(client, tmp_path):
    """Unsupported file type must return 400."""
    bad_file = tmp_path / "test.xyz"
    bad_file.write_bytes(b"not an image")
    with bad_file.open("rb") as fh:
        resp = client.post(
            "/generate-3d", files={"image": ("test.xyz", fh, "application/octet-stream")}
        )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]
