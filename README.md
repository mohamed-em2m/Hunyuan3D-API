# Hunyuan3D API

> FastAPI-based REST API for generating 3D GLB models from images using the **Hunyuan3D** pipeline.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **3D generation** | Hunyuan3D pipeline → `.glb` mesh output |
| **REST API** | FastAPI with OpenAPI docs at `/docs` |
| **Configuration** | [dynaconf](https://www.dynaconf.com/) — TOML + env-vars + secrets file |
| **Package management** | [uv](https://docs.astral.sh/uv/) |
| **Docker** | Multi-stage build with uv |
| **Structured logging** | Python `logging` throughout, log-level from settings |

---

## 🚀 Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed
- Python 3.12
- CUDA-capable GPU (recommended) — CPU inference is supported but very slow
- `hy3dgen` built from source (see **hy3dgen setup** below)

### 1. Clone & enter the project

```bash
git clone https://github.com/your-org/hunyuan3d-api.git
cd hunyuan3d-api
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure

Copy the example env file and edit as needed:

```bash
cp .env.example .env
```

Or create a `.secrets.toml` (gitignored) for tokens:

```toml
# .secrets.toml
[default]
[default.ngrok]
authtoken = "your_ngrok_token"
```

Set the active environment (default is `default`):

```bash
export ENV_FOR_DYNACONF=development   # enables debug logging + auto-reload
```

### 4. Run the API

```bash
# Via the installed CLI script
uv run hunyuan3d-api

# Or via uvicorn directly
uv run uvicorn hunyuan3d_api.main:app --reload

# Or via the root shim
uv run python main.py
```

API docs: <http://localhost:8000/docs>

---

## ⚙️ Configuration Reference

All settings live in [`config/settings.toml`](config/settings.toml).
Override any value without touching the file:

| Method | Example |
|---|---|
| `.env` file | `HUNYUAN3D__SERVER__PORT=9000` |
| `.secrets.toml` | `[default.ngrok] authtoken = "..."` |
| Shell env var | `export HUNYUAN3D__MODEL__DEVICE=cpu` |
| `ENV_FOR_DYNACONF` | `development` / `production` |

Key settings:

```toml
[default.server]
host = "0.0.0.0"
port = 8000

[default.model]
pretrained_id = "tencent/Hunyuan3D-2"
device = "auto"          # auto | cuda | cpu

[default.storage]
temp_dir = "./temp_3d"
max_file_size_mb = 10

[default.ngrok]
enabled = false
authtoken = ""           # set in .secrets.toml
```

---

## 📁 Project Structure

```
hunyuan3d-api/
├── hunyuan3d_api/              # Main Python package
│   ├── config/
│   │   └── __init__.py         # dynaconf Settings object
│   ├── core/
│   │   ├── model_manager.py    # Thread-safe pipeline singleton
│   │   └── utils.py            # File validation & cleanup helpers
│   ├── api/
│   │   └── routes.py           # FastAPI APIRouter (all endpoints)
│   ├── app.py                  # FastAPI app factory
│   └── main.py                 # Package entrypoint + uvicorn launcher
├── config/
│   └── settings.toml           # dynaconf base configuration
├── .secrets.toml               # Secret overrides (gitignored)
├── .env.example                # Documented env-var template
├── main.py                     # Root shim for backwards-compat
├── Dockerfile                  # Multi-stage Docker build
└── pyproject.toml              # uv project + ruff/mypy/pytest config
```

---

## 🖼️ API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service info & health check |
| `GET` | `/health` | Pipeline status, CUDA info |
| `POST` | `/generate-3d` | Upload image → receive `.glb` |
| `GET` | `/docs` | Interactive OpenAPI documentation |

### Example: generate a 3D model

```bash
curl -X POST "http://localhost:8000/generate-3d" \
  -F "image=@/path/to/input.jpg" \
  --output model.glb
```

---

## 🐳 Docker

```bash
# Build
docker build -t hunyuan3d-api .

# Run
docker run -p 8000:8000 \
  -e HUNYUAN3D__NGROK__AUTHTOKEN=your_token \
  hunyuan3d-api
```

> **Note:** The Docker build compiles `hy3dgen` from source (the ComfyUI wrapper).
> First build will take several minutes.

---

## 🔧 hy3dgen Setup (local, non-Docker)

`hy3dgen` is not published on PyPI. Install it from source:

```bash
# 1. Clone the ComfyUI wrapper (contains hy3dgen)
git clone https://github.com/kijai/ComfyUI-Hunyuan3DWrapper.git

# 2. Build and install the custom rasterizer
cd ComfyUI-Hunyuan3DWrapper/hy3dgen/texgen/custom_rasterizer
python setup.py bdist_wheel
pip install dist/*.whl

# 3. Install remaining hy3dgen deps
cd ../../../..
pip install -r ComfyUI-Hunyuan3DWrapper/requirements.txt

# 4. Install Hunyuan3D-2
git clone https://github.com/Tencent/Hunyuan3D-2.git
cd Hunyuan3D-2 && python setup.py install
```

---

## 🧹 Dev Tools

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type-check
uv run mypy hunyuan3d_api/

# Tests
uv run pytest
```

---

## 🧩 Environments

| `ENV_FOR_DYNACONF` | Log level | Reload | Workers |
|---|---|---|---|
| `default` | INFO | off | 1 |
| `development` | DEBUG | on | 1 |
| `production` | WARNING | off | 4 |
