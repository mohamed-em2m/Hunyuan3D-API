import os
import tempfile
import uuid
import asyncio
import logging
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch
import trimesh
from pyngrok import ngrok
import aiofiles
import nest_asyncio

# Enable nested asyncio (required for Colab)
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CELL 3: FastAPI App Setup ===
app = FastAPI(
    title="3D Model Generator API",
    description="Generate 3D models from images using Hunyuan3D (Colab Version)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Colab-specific paths
TEMP_DIR = Path("./temp_3d")
TEMP_DIR.mkdir(exist_ok=True)

# Supported image formats
SUPPORTED_FORMATS = {"jpg", "jpeg", "png", "webp", "bmp"}

# === CELL 4: Model Manager ===
class ModelManager:
    """Singleton class to manage the 3D model pipeline"""
    _instance = None
    _pipeline = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_pipeline(self):
        if self._pipeline is None:
            print("Loading Hunyuan3D pipeline...")
            try:
                # Import here to avoid issues if package isn't installed
                from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
                self._pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
                    'tencent/Hunyuan3D-2'
                )
                print("Pipeline loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load pipeline: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")
        return self._pipeline

model_manager = ModelManager()

# === CELL 5: Utility Functions ===
def cleanup_file(file_path: str):
    """Background task to clean up temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up {file_path}: {e}")

async def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Check file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Reset file position
    await file.seek(0)

async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Save uploaded file"""
    content = await upload_file.read()
    async with aiofiles.open(destination, 'wb') as f:
        await f.write(content)

# === CELL 6: API Endpoints ===
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "3D Model Generator API (Colab Version)",
        "status": "healthy",
        "supported_formats": list(SUPPORTED_FORMATS),
        "temp_dir": str(TEMP_DIR)
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "pipeline_loaded": model_manager._pipeline is not None,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "temp_dir": str(TEMP_DIR)
    }

@app.post("/generate-3d")
async def generate_3d_model(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Image file to convert to 3D model")
):
    """Generate a 3D model from an uploaded image"""
    print("getted request for generat")
    await validate_image(image)

    request_id = str(uuid.uuid4())
    input_path = TEMP_DIR / f"input_{request_id}.jpg"
    output_path = TEMP_DIR / f"output_{request_id}.glb"

    try:
        print(f"Processing request {request_id}")

        # Save uploaded file
        await save_upload_file(image, input_path)
        print(f"Saved input: {input_path}")

        # Get pipeline
        pipeline = await model_manager.get_pipeline()

        # Generate 3D model
        print("Generating 3D model...")
        mesh_result = pipeline(image=str(input_path))

        if not mesh_result or len(mesh_result) == 0:
            raise HTTPException(status_code=500, detail="Failed to generate 3D model")

        mesh = mesh_result[0]

        # Convert to trimesh and export
        print("Converting to GLB...")
        trimesh_obj = trimesh.Trimesh(
            vertices=mesh.vertices,
            faces=mesh.faces,
            process=False
        )

        trimesh_obj.export(str(output_path))
        print(f"Model saved: {output_path}")

        # Schedule cleanup
        background_tasks.add_task(cleanup_file, str(input_path))
        background_tasks.add_task(cleanup_file, str(output_path))

        return FileResponse(
            path=str(output_path),
            media_type="model/gltf-binary",
            filename=f"model_{request_id}.glb"
        )

    except Exception as e:
        background_tasks.add_task(cleanup_file, str(input_path))
        background_tasks.add_task(cleanup_file, str(output_path))
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
