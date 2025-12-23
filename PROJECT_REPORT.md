# Project Report: Life From AI

## 1. Executive Summary
The **Life From AI** is a production-grade Python application designed to automate the creation of narrated videos. It takes a PDF document (specifically the Bhagwat Gita) and a static image of a speaker (Lord Krishna), and generates a video where the avatar lip-syncs perfectly to the narrated text.

The system supports multiple languages (English and Hindi), handles large texts via intelligent chunking, and utilizes state-of-the-art Generative Adversarial Networks (GANs) for realistic facial animation.

---

## 2. System Architecture

The application follows a modular pipeline architecture. Data flows sequentially through three distinct stages:

1.  **Text Extraction Module**: Parses raw PDF data into clean, readable text.
2.  **Audio Synthesis Module (TTS)**: Converts text into high-fidelity neural speech.
3.  **Video Synthesis Module (Wav2Lip)**: Synchronizes the avatar's lip movements with the generated audio.

### High-Level Data Flow
```mermaid
[Input PDF] --> [PDF Extractor] --> [Clean Text]
                                      |
                                      v
                                [TTS Generator] --> [Audio File (.mp3)]
                                      |
                                      v
[Input Avatar] ----------------> [Wav2Lip GAN] --> [Output Video (.mp4)]
```

---

## 3. Technology Stack

The project leverages a combination of standard media libraries and advanced AI models:

### Core Technologies
*   **Python 3.10**: The primary programming language. Version 3.10 is specifically chosen to maintain compatibility with older deep learning libraries required by Wav2Lip.
*   **FFmpeg**: The backbone of all media processing. It is used for combining audio chunks, merging audio with video, and handling video codecs.

### Libraries & Modules
1.  **PDF Processing (`pdfplumber`)**:
    *   Used for extracting text from PDFs.
    *   Chosen over `PyPDF2` for its superior ability to handle layout analysis and text extraction accuracy.
2.  **Text-to-Speech (`edge-tts`)**:
    *   A Python wrapper for Microsoft Edge's online Text-to-Speech service.
    *   **Why used?** It provides "Neural" voices (e.g., `en-IN-PrabhatNeural`, `hi-IN-MadhurNeural`) that sound human-like, without requiring heavy local GPU resources for TTS.
3.  **Lip-Syncing (`Wav2Lip`)**:
    *   A deep learning model based on GANs (Generative Adversarial Networks).
    *   It takes a face image and an audio segment as input and generates video frames where the mouth moves in sync with the phonemes of the audio.
    *   **Dependencies**: `PyTorch`, `NumPy` (v1.23.5), `Librosa` (v0.8.1), `OpenCV`.

---

## 4. AI & Machine Learning Deep Dive

This project is not just a script; it is an integration of multiple advanced AI disciplines.

### 4.1. Generative Adversarial Networks (GANs)
The core of the video generation is **Wav2Lip**, a GAN-based model designed for lip-syncing.

*   **The Generator**: Takes a face image (with the lower half masked) and an audio segment (Mel-spectrogram) as input. It tries to generate the missing mouth region that matches the audio.
*   **The Discriminator**: A pre-trained "Lip-Sync Expert" that evaluates if the generated mouth movement is synchronized with the audio.
*   **Training Objective**: The generator learns to fool the discriminator by creating highly realistic and synchronized lip movements.

### 4.2. Audio Processing (Mel-Spectrograms)
Before the audio can be used by the GAN, it must be converted into a format the machine understands.
*   **Mel-Spectrogram**: A visual representation of the audio's frequency spectrum.
*   **Process**: The raw audio waveform is processed using Short-Time Fourier Transform (STFT) to extract frequency features, which are then mapped to the Mel scale (mimicking human hearing).
*   **Role**: These spectrograms serve as the "condition" for the GAN, telling it exactly what shape the mouth should be in for a given phoneme (sound unit).

### 4.3. Face Detection (S3FD)
To modify only the lips, the system must first know where the face is.
*   **Model**: **S3FD (Single Shot Scale-invariant Face Detector)**.
*   **Function**: It scans the input image/video frame and returns the bounding box coordinates of the face.
*   **Precision**: This ensures that the GAN only modifies the relevant pixels (the mouth area) while keeping the rest of the face (eyes, nose, background) intact.

### 4.4. Neural Text-to-Speech (TTS) Architecture
The project utilizes **Microsoft Edge's Neural TTS**, which represents the cutting edge of speech synthesis. Unlike older technologies, it does not just read words; it understands context.

*   **Evolution of TTS**:
    *   **Concatenative TTS**: Used small pre-recorded sound clips glued together. Result: Robotic and disjointed.
    *   **Parametric TTS**: Generated speech using mathematical models (vocoders). Result: Smoother but muffled/buzzy.
    *   **Neural TTS (End-to-End)**: Uses Deep Neural Networks (DNNs) to map text directly to acoustic features (spectrograms) and then to audio waveforms.

*   **Underlying Technology (Transformer Models)**:
    *   Modern Neural TTS (like the one used here) typically relies on **Transformer architectures** (similar to BERT or GPT-3 but for audio).
    *   **Prosody Prediction**: The model predicts pitch, duration, and volume for each phoneme based on the sentence context. This allows it to pause correctly at commas and intonate questions properly.
    *   **HiFi-GAN Vocoder**: The final step often involves a GAN-based vocoder (like HiFi-GAN) to convert the generated spectrograms into high-fidelity audio waveforms that sound indistinguishable from human recordings.

*   **Relevance to Bhagwat Gita**:
    *   For a spiritual text, **solemnity and correct pacing** are crucial. The Neural TTS engine automatically adjusts its cadence to match the sentence structure of the verses, providing a respectful and engaging narration without manual tuning.

---

## 5. Detailed Workflow & Execution Logic

### Step 1: Initialization & Configuration
The entry point is `main.py` (or `demo.sh`). The system loads configurations from `src/config.py`, ensuring all paths (assets, outputs, models) are defined centrally. It sets up a logger to track the execution process.

### Step 2: Intelligent Text Extraction
**Module:** `src/pdf_extractor.py`

*   **Input**: PDF Path, Chapter Number.
*   **Process**:
    1.  Opens the PDF using `pdfplumber`.
    2.  **Cleaning**: Removes hyphenation (e.g., "exam-\nple" -> "example") and normalizes whitespace.
    3.  **Chapter Segmentation**: If a chapter number is provided, the system uses heuristic pattern matching (looking for "Chapter X", "Adhyay X") to locate the start and end indices of the specific chapter.
*   **Output**: A clean string of text.

### Step 3: Audio Generation (Chunking Strategy)
**Module:** `src/tts_generator.py`

*   **Challenge**: TTS services often have character limits or timeout issues with long texts (like a full chapter).
*   **Solution**:
    1.  The text is split into chunks of 2000 characters.
    2.  Each chunk is sent to the `edge-tts` API asynchronously.
    3.  Temporary audio files (`chunk_0.mp3`, `chunk_1.mp3`...) are generated.
    4.  **Merging**: `FFmpeg` is invoked to concatenate these chunks seamlessly into a single `output_audio.mp3`.
*   **Output**: A complete audio file of the narration.

### Step 4: Video Synthesis (The AI Core)
**Module:** `src/video_generator.py` & `Wav2Lip/inference.py`

This is the most computationally intensive part.

1.  **Validation**: Checks if the Wav2Lip model weights (`wav2lip_gan.pth`) and face detection model (`s3fd.pth`) exist.
2.  **Face Detection**: The system uses the `s3fd` model to locate the face in the `krishna.jpg` image.
3.  **Mel-Spectrogram Generation**: The audio is analyzed to create Mel-spectrograms (visual representation of audio frequencies over time).
4.  **Inference**:
    *   The Wav2Lip GAN takes the static face frame and the audio spectrograms.
    *   For every audio frame, it generates a corresponding video frame where the lips are modified to match the sound.
    *   The background and upper face remain largely static (preserving the original image quality), while the mouth region is regenerated.
5.  **Assembly**: The generated frames are combined with the original audio using `FFmpeg` to create the final MP4.

---

## 6. Multi-Language Demo Generation

The project includes a unified automation script (`demo.sh`) that demonstrates the system's capability to handle multiple languages seamlessly.

### How `demo.sh` Works
The script executes the entire pipeline twice in sequence, once for English and once for Hindi.

#### 1. English Generation (`output_english.mp4`)
*   **Input**: `gita_demo.pdf` (English text).
*   **Command**: `python main.py --lang en ...`
*   **TTS Voice**: Uses `en-IN-PrabhatNeural` (Indian English accent).
*   **Process**:
    1.  Extracts English text from the PDF.
    2.  Generates English audio.
    3.  Lip-syncs the avatar to the English audio.

#### 2. Hindi Generation (`output_hindi.mp4`)
*   **Input**: `gita_demo_hindi.pdf` (Generated PDF with real Hindi font).
*   **Command**: `python main.py --lang hi ...`
*   **TTS Voice**: Uses `hi-IN-MadhurNeural` (Natural Hindi).
*   **Process**:
    1.  Extracts Hindi text from the PDF.
    2.  Generates Hindi audio.
    3.  Lip-syncs the avatar to the Hindi audio.

This dual-execution approach proves that the core architecture (Wav2Lip + EdgeTTS) is language-agnostic. The lip-syncing model works purely on audio phonemes, meaning it can animate the avatar to speak **any language** provided the audio is clear.

---

## 7. Project Structure

```text
BhagwatGitaNarrator/
├── assets/                  # Input media (krishna.jpg)
├── outputs/                 # Generated videos go here
├── src/                     # Source Code
│   ├── config.py            # Central configuration
│   ├── pdf_extractor.py     # Text extraction logic
│   ├── tts_generator.py     # Audio generation logic
│   └── video_generator.py   # Wrapper for Wav2Lip
├── Wav2Lip/                 # The AI Model Submodule
│   ├── checkpoints/         # Contains wav2lip_gan.pth
│   └── inference.py         # Core inference script
├── demo.sh                  # Master script to run demos
├── main.py                  # Main Python entry point
├── requirements.txt         # Python dependencies
└── setup_wav2lip.sh         # Environment setup script
```

---

## 8. Challenges & Solutions

During development, several compatibility issues were solved to make this "Production Grade":

1.  **Dependency Hell**: Wav2Lip relies on older versions of `librosa` and `numpy`.
    *   *Solution*: The `setup_wav2lip.sh` script strictly pins `numpy==1.23.5` and `librosa==0.8.1`, preventing conflicts with newer libraries like `numba`.
2.  **Long Text Handling**:
    *   *Solution*: Implemented a robust chunking mechanism in `tts_generator.py` to handle chapters of any length without API timeouts.
3.  **PDF Formatting**:
    *   *Solution*: Custom Regex cleaning in `pdf_extractor.py` ensures the narrated text flows naturally, removing artifacts like page headers or line breaks.

## 9. Future Improvements

*   **Blinking & Head Movement**: Currently, the video is a lip-synced static image. Future versions could use "MakeItTalk" or similar models to add head nods and eye blinks.
*   **Subtitle Overlay**: Using `FFmpeg` to burn the extracted text onto the video as subtitles.
*   **Background Music**: Mixing a low-volume flute track behind the narration for ambiance.
