# Bhagwat Gita Narrator

This project generates a video narration of the Bhagwat Gita using an AI avatar (Lord Krishna) that lip-syncs to the text.

## Prerequisites

1.  **Python 3.8+**
2.  **FFmpeg**: `brew install ffmpeg`
3.  **Wav2Lip**: Required for realistic lip-syncing.

## Setup

1.  **Create Environment**:
    ```bash
    conda create -n gita_env python=3.10 -y
    conda activate gita_env
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Wav2Lip**:
    Run the setup script. This will automatically download the required models.
    ```bash
    chmod +x setup_wav2lip.sh
    ./setup_wav2lip.sh
    ```

4.  **Add Assets**:
    *   **PDF**: Place your `gita.pdf` in the root folder.
    *   **Image**: Place a high-quality image of Lord Krishna at `assets/krishna.jpg`.

## Usage

### Run Demo (English & Hindi)
This single script generates both demos and saves them to the `outputs/` folder.

```bash
chmod +x demo.sh
./demo.sh
```

### Run Manually
To narrate a specific chapter from your own PDF:

```bash
python main.py --pdf_path gita.pdf --lang en --chapter 1 --output outputs/my_video.mp4
```

*   `--pdf_path`: Path to the PDF file.
*   `--lang`: Language (`en` for English, `hi` for Hindi).
*   `--chapter`: Specific chapter number.
*   `--output`: Output video filename.

## Troubleshooting

*   **Wav2Lip Errors**: Ensure you are using Python 3.10 and have run `setup_wav2lip.sh` successfully.
*   **Face Detection**: Ensure the `krishna.jpg` has a clear, frontal face.
