# Knowledge To Life

Turn your static PDF documents into an interactive, talking AI avatar. This application allows you to upload a document, ask questions, and receive answers delivered by a realistic, lip-synced digital persona.

## Features
*   **Offline RAG**: Securely processes documents on your local machine using LangChain and FAISS.
*   **AI Video Generation**: Uses Wav2Lip to animate any static face image to speak the AI's response.
*   **Custom Avatars**: Upload your own image to be the face of your knowledge base.
*   **Neural TTS**: High-quality voice synthesis using Edge-TTS.

## Prerequisites
*   **Python 3.10** (Recommended)
*   **FFmpeg**: Required for video processing.
    ```bash
    brew install ffmpeg
    ```

## Installation

1.  **Run the Setup Script**:
    This will install all necessary Python dependencies and fix potential environment conflicts.
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

## Usage

1.  **Start the Application**:
    ```bash
    ./run_chat.sh
    ```
2.  **Upload Knowledge**: Use the sidebar to upload a PDF document.
3.  **Choose Avatar**: Upload your own photo or use the default.
4.  **Chat**: Ask a question in the chat box. The AI will generate a text response immediately, followed by a video response.

## Troubleshooting
*   **Video Generation is Slow**: This is expected on CPU. The system prioritizes quality and stability over real-time rendering.
*   **Installation Errors**: Ensure you have a clean Python 3.10 environment and run `./setup.sh`.

## License
MIT
