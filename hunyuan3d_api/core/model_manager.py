"""
hunyuan3d_api.core.model_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Thread-safe singleton that owns the Hunyuan3D pipeline lifecycle.
Settings are read from dynaconf at first access.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

import torch
from fastapi import HTTPException

from hunyuan3d_api.config import settings

if TYPE_CHECKING:
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline as _Pipeline

logger = logging.getLogger(__name__)


def _resolve_device() -> str:
    """Return the torch device string based on settings."""
    device_cfg: str = settings.model.device.lower()
    if device_cfg == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device_cfg


class ModelManager:
    """Thread-safe singleton that lazily loads the Hunyuan3D pipeline.

    The pipeline is loaded on the first call to :py:meth:`get_pipeline` and
    reused for all subsequent requests.  Loading is protected by a lock so
    that concurrent startup requests don't trigger double-loading.
    """

    _instance: ModelManager | None = None
    _lock: threading.Lock = threading.Lock()

    # Per-instance state
    _pipeline: _Pipeline | None = None
    _pipeline_lock: threading.Lock

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._pipeline = None
                    inst._pipeline_lock = threading.Lock()
                    cls._instance = inst
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_pipeline(self) -> _Pipeline:
        """Return the loaded pipeline, loading it lazily on first call."""
        if self._pipeline is not None:
            return self._pipeline

        with self._pipeline_lock:
            # Double-checked locking
            if self._pipeline is not None:
                return self._pipeline

            pretrained_id: str = settings.model.pretrained_id
            device = _resolve_device()
            logger.info(
                "Loading Hunyuan3D pipeline from '%s' on device '%s'…", pretrained_id, device
            )

            try:
                # Import lazily so the service can start even when hy3dgen
                # is not installed (useful for health-check-only deployments).
                from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

                self._pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(pretrained_id)
                logger.info("Hunyuan3D pipeline loaded successfully.")
            except ImportError as exc:
                logger.error("hy3dgen is not installed: %s", exc)
                raise HTTPException(
                    status_code=503,
                    detail="hy3dgen package is not installed. See README for setup instructions.",
                ) from exc
            except Exception as exc:
                logger.exception("Failed to load Hunyuan3D pipeline")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load model: {exc}",
                ) from exc

        return self._pipeline

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` if the pipeline has been loaded."""
        return self._pipeline is not None

    @classmethod
    def reset(cls) -> None:
        """Unload the pipeline and reset the singleton (mainly for testing)."""
        if cls._instance is not None:
            cls._instance._pipeline = None


# Module-level singleton — import this everywhere
model_manager = ModelManager()
