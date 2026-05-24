"""
Root-level main.py — thin shim kept for backwards compatibility.

All real logic lives inside the ``hunyuan3d_api`` package.
Prefer running via:
    uv run hunyuan3d-api
or:
    uv run uvicorn hunyuan3d_api.main:app --reload
"""

from hunyuan3d_api.main import app, run  # noqa: F401

if __name__ == "__main__":
    run()
