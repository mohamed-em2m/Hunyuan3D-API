"""
hunyuan3d_api.core.utils
~~~~~~~~~~~~~~~~~~~~~~~~~
Shared async utility helpers for file handling.
Settings-driven limits (max file size, supported formats).
"""

from __future__ import annotations

import logging
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile

from hunyuan3d_api.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers derived from settings
# ---------------------------------------------------------------------------


def get_supported_formats() -> set[str]:
    """Return the set of allowed image extensions (lower-case, no dot)."""
    return {fmt.lower() for fmt in settings.storage.supported_formats}


def get_max_file_bytes() -> int:
    """Return the maximum allowed upload size in bytes."""
    return int(settings.storage.max_file_size_mb) * 1024 * 1024


def get_temp_dir() -> Path:
    """Return (and create if needed) the temp directory from settings."""
    tmp = Path(settings.storage.temp_dir)
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def cleanup_file(file_path: str | Path) -> None:
    """Remove a temporary file — intended as a FastAPI ``BackgroundTask``."""
    path = Path(file_path)
    try:
        if path.exists():
            path.unlink()
            logger.debug("Cleaned up temp file: %s", path)
    except OSError:
        logger.warning("Could not delete temp file: %s", path, exc_info=True)


async def validate_image(file: UploadFile) -> None:
    """Validate an uploaded image file against configured limits.

    Raises :class:`fastapi.HTTPException` (400) if validation fails.
    """
    supported = get_supported_formats()
    max_bytes = get_max_file_bytes()

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '.{extension}'. Supported: {', '.join(sorted(supported))}",
        )

    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(content) / 1_048_576:.1f} MB). "
            f"Maximum allowed: {settings.storage.max_file_size_mb} MB.",
        )

    # Reset stream position so downstream handlers can re-read the content
    await file.seek(0)


async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Persist an :class:`~fastapi.UploadFile` to *destination* asynchronously."""
    content = await upload_file.read()
    async with aiofiles.open(destination, "wb") as fh:
        await fh.write(content)
    logger.debug("Saved uploaded file → %s (%d bytes)", destination, len(content))
