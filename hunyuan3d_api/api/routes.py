"""
hunyuan3d_api.api.routes
~~~~~~~~~~~~~~~~~~~~~~~~~
All FastAPI route handlers, extracted from the flat main.py into a proper
APIRouter so they can be mounted by the app factory in app.py.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import torch
import trimesh
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse

from hunyuan3d_api.config import settings
from hunyuan3d_api.core.model_manager import model_manager
from hunyuan3d_api.core.utils import (
    cleanup_file,
    get_temp_dir,
    save_upload_file,
    validate_image,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health / status
# ---------------------------------------------------------------------------


@router.get("/", tags=["health"], summary="Basic health check")
async def root() -> dict:
    """Return a brief status message confirming the service is running."""
    return {
        "service": settings.app.name,
        "version": settings.app.version,
        "status": "healthy",
        "supported_formats": sorted(settings.storage.supported_formats),
    }


@router.get("/health", tags=["health"], summary="Detailed health status")
async def health_check() -> dict:
    """Return detailed health information including pipeline and GPU status."""
    cuda_available = torch.cuda.is_available()
    return {
        "status": "healthy",
        "pipeline_loaded": model_manager.is_loaded,
        "cuda_available": cuda_available,
        "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
        "model_id": settings.model.pretrained_id,
        "temp_dir": settings.storage.temp_dir,
    }


# ---------------------------------------------------------------------------
# 3-D generation
# ---------------------------------------------------------------------------


@router.post(
    "/generate-3d",
    tags=["generation"],
    summary="Generate a 3D GLB model from an uploaded image",
    response_description="Binary GLB file",
)
async def generate_3d_model(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Image file to convert to 3D model"),  # noqa: B008
) -> FileResponse:
    """Upload an image and receive a `.glb` 3D model.

    Supported formats: JPEG, PNG, WebP, BMP.
    Maximum file size: configurable via `storage.max_file_size_mb`.
    """
    await validate_image(image)

    request_id = str(uuid.uuid4())
    temp_dir: Path = get_temp_dir()
    input_path = temp_dir / f"input_{request_id}.jpg"
    output_path = temp_dir / f"output_{request_id}.glb"

    # Always schedule cleanup (runs even if an exception is raised below)
    background_tasks.add_task(cleanup_file, input_path)
    background_tasks.add_task(cleanup_file, output_path)

    try:
        logger.info("Processing request %s", request_id)

        await save_upload_file(image, input_path)
        logger.debug("Input saved → %s", input_path)

        pipeline = await model_manager.get_pipeline()

        logger.info("Generating 3D model for request %s …", request_id)
        mesh_result = pipeline(image=str(input_path))

        if not mesh_result:
            raise ValueError("Pipeline returned an empty result.")

        mesh = mesh_result[0]

        logger.debug("Converting mesh to GLB …")
        trimesh_obj = trimesh.Trimesh(
            vertices=mesh.vertices,
            faces=mesh.faces,
            process=False,
        )
        trimesh_obj.export(str(output_path))
        logger.info("GLB saved → %s", output_path)

        return FileResponse(
            path=str(output_path),
            media_type="model/gltf-binary",
            filename=f"model_{request_id}.glb",
        )

    except Exception as exc:
        logger.exception("Failed to process request %s: %s", request_id, exc)
        # Re-raise so FastAPI returns a proper 500 JSON response
        raise
