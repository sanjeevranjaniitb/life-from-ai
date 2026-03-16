#!/bin/bash

echo "--- Running Aggressive Environment Setup ---"

# Check for FFMPEG
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it using: brew install ffmpeg"
    exit 1
fi

# Create directories
mkdir -p outputs
mkdir -p temp

# --- Step 1: Fix Corrupted Environment ---
echo "Attempting to fix corrupted 'certifi' package..."
pip install --ignore-installed certifi

# --- Step 2: Install Pinned Dependencies ---
echo "Installing stable, pinned versions of AI/ML libraries..."
pip install -r requirements.txt

echo "---"
echo "Setup Complete! The environment should now be stable."
echo "You can now run the application with: ./run_chat.sh"
echo "---"
