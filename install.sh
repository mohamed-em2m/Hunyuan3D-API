#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Install necessary Python packages
pip install hy3dgen
pip install --upgrade huggingface_hub
pip install gradio

# Clone required GitHub repositories
git clone https://github.com/Tencent/Hunyuan3D-2.git
git clone https://github.com/kijai/ComfyUI-Hunyuan3DWrapper.git

# Install requirements for the wrapper
pip install -r ComfyUI-Hunyuan3DWrapper/requirements.txt

# Build the custom rasterizer wheel
cd ComfyUI-Hunyuan3DWrapper/hy3dgen/texgen/custom_rasterizer/
python setup.py bdist_wheel

# Install the built wheel (adjust filename if necessary)
pip install dist/custom_rasterizer*.whl

# Install Hunyuan3D-2 package
python ../../../../../Hunyuan3D-2/setup.py install

# Return to the original directory
cd ../../../../..