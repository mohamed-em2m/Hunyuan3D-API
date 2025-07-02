FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
       build-essential \
       git \
       curl \
       gnupg \
       ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Add ngrok repository and install
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
      | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
      | tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && \
    apt-get install -y ngrok && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone repositories
RUN git clone https://github.com/Tencent/Hunyuan3D-2.git && \
    git clone https://github.com/kijai/ComfyUI-Hunyuan3DWrapper.git

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn aiofiles pyngrok python-multipart trimesh torch torchvision gradio hy3dgen huggingface_hub

# Install ComfyUI wrapper requirements
RUN pip install -r ComfyUI-Hunyuan3DWrapper/requirements.txt

# Build and install custom rasterizer wheel
WORKDIR /app/ComfyUI-Hunyuan3DWrapper/hy3dgen/texgen/custom_rasterizer
RUN python setup.py bdist_wheel && \
    pip install dist/*.whl

# Install Hunyuan3D-2
WORKDIR /app/Hunyuan3D-2
RUN python setup.py install

# Cleanup build tools
FROM python:3.12-slim
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
WORKDIR /app

# Expose API port
EXPOSE 8000

# Default command
CMD ["uvicorn", "your_fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
