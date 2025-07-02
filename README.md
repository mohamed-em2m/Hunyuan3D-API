# 3D Model Generator API

This project provides a **FastAPI**-based REST API to generate 3D models from images using the **Hunyuan3D** pipeline. It includes a Docker setup for easy deployment, support for **ngrok** tunneling, and background cleanup of temporary files.

---

## 📦 Features

- **FastAPI** server with CORS support
- **Hunyuan3D** pipeline for 3D mesh generation
- **Trimesh** for mesh handling and GLB export
- **ngrok** integration for public URL tunneling
- **Async file handling** via `aiofiles`
- **Background cleanup** of temporary uploads
- **Docker** multi-stage build for a lean production image

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Run with Docker

1. **Build the Docker image**:
   ```bash
docker build -t 3dmodel-api .
```
2. **Run the container**:
   ```bash
docker run -p 8000:8000 3dmodel-api
```
3. **Access API docs** at: <http://localhost:8000/docs>

### 3. Run Locally (without Docker)

1. **Create and activate** a virtual environment:
   ```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
2. **Install dependencies**:
   ```bash
pip install -r requirements.txt
```
3. **Start the server**:
   ```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
4. **Explore** at: <http://localhost:8000/docs>

---

## ⚙️ Configuration

- **TEMP_DIR**: Default is `/content/temp_3d`. Change in `main.py` if needed.
- **NGROK**: For tunneling (e.g., Colab), set your ngrok token:
  ```bash
  export NGROK_AUTHTOKEN=<your-token>
  ```

---

## 🛠️ Project Structure

```text
├── Dockerfile                # Multi-stage Docker build
├── requirements.txt          # Python dependencies
├── main.py                   # FastAPI application
├── temp_3d/                  # Runtime uploads & outputs
└── README.md                 # Project documentation
```

---

## 🖼️ API Endpoints

| Method | Path           | Description                             |
| ------ | -------------- | --------------------------------------- |
| GET    | `/`            | Basic health check                      |
| GET    | `/health`      | Detailed health status (pipeline, GPU)  |
| POST   | `/generate-3d` | Upload an image and receive a `.glb`    |

### Example: Generate 3D Model

```bash
curl -X POST "http://localhost:8000/generate-3d" \
  -F "image=@/path/to/input.jpg" \
  --output model.glb
```

---

## 🧹 Cleanup

Temporary files are automatically removed in the background after each request.


