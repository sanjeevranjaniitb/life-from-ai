#!/bin/bash

echo "Setting up Wav2Lip for realistic lip-syncing..."

# 1. Install Dependencies via Conda (Preferred for Mac to avoid compilation issues)
echo "Installing dependencies via Conda..."
if command -v conda &> /dev/null; then
    # Install base dependencies
    conda install -y -c pytorch pytorch torchvision
    conda install -y -c conda-forge ffmpeg cmake
    conda install -y -c conda-forge librosa=0.8.1 numba llvmlite scipy tqdm
else
    echo "Conda not found. This script is optimized for Conda environments on Mac."
    exit 1
fi

# 2. Install remaining dependencies via Pip
echo "Installing remaining dependencies via Pip..."
# We install an older version of opencv-python that supports numpy 1.x
# opencv-python 4.8.0.74 is generally stable with numpy 1.23.x
pip install "opencv-python==4.8.0.74"

# 3. FORCE DOWNGRADE NUMPY
# This is the critical step. Pip or Conda might have upgraded numpy during previous steps.
# We force it back to 1.23.5 which works for both librosa 0.8.1 and numba.
echo "Forcing NumPy version to 1.23.5..."
pip install "numpy==1.23.5" --force-reinstall

# 4. Clone Wav2Lip Repository
if [ ! -d "Wav2Lip" ]; then
    echo "Cloning Wav2Lip repository..."
    git clone https://github.com/Rudrabha/Wav2Lip.git
else
    echo "Wav2Lip repository already exists."
fi

# 5. Download Model Weights automatically
echo "Creating checkpoints directory..."
mkdir -p Wav2Lip/checkpoints

echo "Downloading Wav2Lip GAN Model (wav2lip_gan.pth)..."
if [ ! -f "Wav2Lip/checkpoints/wav2lip_gan.pth" ]; then
    curl -L -o Wav2Lip/checkpoints/wav2lip_gan.pth https://huggingface.co/camenduru/Wav2Lip/resolve/main/checkpoints/wav2lip_gan.pth
    if [ $? -eq 0 ]; then
        echo "Model downloaded successfully!"
    else
        echo "Download failed. Please try downloading manually from: https://huggingface.co/camenduru/Wav2Lip/tree/main/checkpoints"
        exit 1
    fi
else
    echo "Model already exists."
fi

# 6. Download Face Detection Model (s3fd)
echo "Downloading Face Detection Model (s3fd.pth)..."
mkdir -p Wav2Lip/face_detection/detection/sfd/
if [ ! -f "Wav2Lip/face_detection/detection/sfd/s3fd.pth" ]; then
    curl -L -o Wav2Lip/face_detection/detection/sfd/s3fd.pth https://huggingface.co/camenduru/Wav2Lip/resolve/main/face_detection/detection/sfd/s3fd.pth
else
    echo "Face detection model already exists."
fi

echo "========================================================"
echo "Setup Complete! You can now run the project."
echo "========================================================"
