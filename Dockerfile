# =============================================================================
# Hunyuan3D-API — Multi-stage Dockerfile
#
# Stage 1 (builder): install system deps, clone Hunyuan3D source, build
#                    the custom rasterizer wheel, install hy3dgen.
# Stage 2 (runtime): copy only what's needed from builder + install the
#                    Python package via uv.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install system build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
       build-essential \
       git \
       curl \
       gnupg \
       ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Clone Hunyuan3D-2 and the ComfyUI wrapper (contains hy3dgen + custom rasterizer)
RUN git clone --depth=1 https://github.com/Tencent/Hunyuan3D-2.git && \
    git clone --depth=1 https://github.com/kijai/ComfyUI-Hunyuan3DWrapper.git

# Build the custom rasterizer wheel
WORKDIR /build/ComfyUI-Hunyuan3DWrapper/hy3dgen/texgen/custom_rasterizer
RUN python setup.py bdist_wheel

# Install hy3dgen and the custom rasterizer into a shared site-packages prefix
WORKDIR /build
RUN pip install --prefix=/install --no-cache-dir \
        ComfyUI-Hunyuan3DWrapper/hy3dgen/texgen/custom_rasterizer/dist/*.whl && \
    pip install --prefix=/install --no-cache-dir \
        -r ComfyUI-Hunyuan3DWrapper/requirements.txt && \
    cd Hunyuan3D-2 && python setup.py install --prefix=/install

# -----------------------------------------------------------------------------
# Stage 2: runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy hy3dgen + custom rasterizer from builder
COPY --from=builder /install /usr/local

# Set working directory and copy project source
WORKDIR /app
COPY pyproject.toml ./
COPY hunyuan3d_api/ ./hunyuan3d_api/
COPY config/ ./config/
COPY .env.example ./.env.example
COPY main.py ./

# Install Python dependencies (excluding hy3dgen — already handled above)
RUN uv pip install --system --no-cache \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "aiofiles>=24.1.0" \
    "python-multipart>=0.0.12" \
    "trimesh>=4.5.0" \
    "torch>=2.5.0" \
    "torchvision>=0.20.0" \
    "huggingface-hub>=0.26.0" \
    "numpy>=1.26.0" \
    "Pillow>=11.0.0" \
    "dynaconf>=3.2.0" \
    "pyngrok>=7.2.0"

# Runtime temp directory
RUN mkdir -p /app/temp_3d

# Expose API port
EXPOSE 8000

# Default environment: production
ENV ENV_FOR_DYNACONF=production

# Launch via the package entrypoint
CMD ["python", "-m", "hunyuan3d_api.main"]
