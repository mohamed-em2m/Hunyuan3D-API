"""
hunyuan3d_api.main
~~~~~~~~~~~~~~~~~~~
Package-level entry point wired to the ``hunyuan3d-api`` CLI script
defined in ``pyproject.toml``.

Usage
-----
    # Via uv script (recommended)
    uv run hunyuan3d-api

    # Direct
    uv run python -m hunyuan3d_api.main

    # Or point uvicorn at the module-level 'app' object
    uv run uvicorn hunyuan3d_api.main:app --reload
"""

from __future__ import annotations

import uvicorn

from hunyuan3d_api.app import create_app
from hunyuan3d_api.config import settings

# Module-level app object so uvicorn can reference it by string
# e.g.  uvicorn hunyuan3d_api.main:app
app = create_app()


def run() -> None:
    """Start the uvicorn server — called by the CLI script ``hunyuan3d-api``."""
    uvicorn.run(
        "hunyuan3d_api.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=settings.server.workers if not settings.server.reload else 1,
        log_level=settings.logging.level.lower(),
    )


if __name__ == "__main__":
    run()
