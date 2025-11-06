@echo off
echo Activating virtual environment...
call .venv\Scripts\activate

echo Uninstalling existing torch and tensorflow...
pip uninstall torch -y
pip uninstall tensorflow -y

echo Installing PyTorch with CUDA 11.8 support...
pip install torch==2.1.2 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo Installing TensorFlow with GPU support (requires CUDA 11.2 and cuDNN)...
pip install tensorflow[gpu]==2.9.2

echo GPU dependencies installation complete.
echo IMPORTANT: This script assumes NVIDIA CUDA Toolkit (11.2 recommended for TensorFlow 2.9.2) and cuDNN are already installed and configured on your system.
pause