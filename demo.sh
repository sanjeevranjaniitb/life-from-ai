#!/bin/bash

# Check for FFMPEG
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed."
    echo "Please install it using: brew install ffmpeg"
    exit 1
fi

# Create output directory
mkdir -p outputs

# 1. Generate Demo Assets
echo "Checking demo assets..."
python create_demo_assets.py

# 2. Run English Demo
echo "--------------------------------------------------------"
echo "Running English Demo..."
echo "--------------------------------------------------------"
python main.py --pdf_path gita_demo.pdf --lang en --chapter 1 --output outputs/output_english.mp4

# 3. Run Hindi Demo
echo "--------------------------------------------------------"
echo "Running Hindi Demo..."
echo "--------------------------------------------------------"
python main.py --pdf_path gita_demo_hindi.pdf --lang hi --chapter 1 --output outputs/output_hindi.mp4

# 4. Cleanup
echo "--------------------------------------------------------"
echo "Cleaning up..."
echo "--------------------------------------------------------"

# Remove intermediate files
rm -f output_audio.mp3
rm -f temp/temp.wav
rm -f temp/result.avi
rm -rf temp

# Remove unused/old scripts if they exist
rm -f run_demo.sh run_hindi_demo.sh run_all_demos.sh run.sh

echo "--------------------------------------------------------"
echo "All Demos Completed!"
echo "Outputs saved in 'outputs/' folder:"
echo "  - outputs/output_english.mp4"
echo "  - outputs/output_hindi.mp4"
echo "--------------------------------------------------------"
