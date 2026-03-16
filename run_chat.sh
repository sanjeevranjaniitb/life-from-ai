#!/bin/bash

# Ensure we are using the correct Python executable
# Try to find the conda python first
CONDA_PYTHON=~/anaconda3/envs/gita_env/bin/python

if [ -f "$CONDA_PYTHON" ]; then
    PYTHON_EXEC="$CONDA_PYTHON"
else
    # Fallback to standard python (assumes environment is activated)
    PYTHON_EXEC="python"
fi

# Check for FFMPEG
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed."
    exit 1
fi

mkdir -p outputs
mkdir -p temp

echo "Starting Knowledge To Life using: $PYTHON_EXEC"
"$PYTHON_EXEC" -m streamlit run app.py
