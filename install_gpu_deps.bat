@echo off
echo Activating virtual environment...
call .venv\Scripts\activate

echo Uninstalling existing torch and tensorflow...
pip uninstall torch torchvision torchaudio -y

echo Installing PyTorch with CUDA 11.8 support...
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu118

echo GPU dependencies installation complete.
echo IMPORTANT: This script assumes NVIDIA CUDA Toolkit 11.8 and cuDNN are already installed and configured on your system.
pause