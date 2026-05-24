"""
hunyuan3d_api.app
~~~~~~~~~~~~~~~~~~
FastAPI application factory.

Import ``create_app`` and call it to get a configured ``FastAPI`` instance
with all middleware and routes registered.  Keeping this separate from
``main.py`` makes the app importable by test suites without launching uvicorn.
"""

from __future__ import annotations

import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hunyuan3d_api.api.routes import router
from hunyuan3d_api.config import settings


def _configure_logging() -> None:
    """Apply logging configuration from dynaconf settings."""
    logging.basicConfig(
        level=settings.logging.level.upper(),
        format=settings.logging.format,
    )


def create_app() -> FastAPI:
    """Construct and return the fully configured FastAPI application.

    Returns
    -------
    FastAPI
        Ready-to-serve ASGI application instance.
    """
    _configure_logging()

    app = FastAPI(
        title=settings.app.name,
        description=settings.app.description,
        version=settings.app.version,
        debug=settings.app.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors.allow_origins),
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=list(settings.cors.allow_methods),
        allow_headers=list(settings.cors.allow_headers),
    )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(router)

    return app
