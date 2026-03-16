import os

# --- Project Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
WAV2LIP_DIR = os.path.join(BASE_DIR, "Wav2Lip")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Default Assets ---
DEFAULT_AVATAR_PATH = os.path.join(ASSETS_DIR, "krishna.jpg")

# --- Wav2Lip Settings ---
WAV2LIP_CHECKPOINT = os.path.join(WAV2LIP_DIR, "checkpoints", "wav2lip_gan.pth")
WAV2LIP_INFERENCE_SCRIPT = os.path.join(WAV2LIP_DIR, "inference.py")

# --- TTS Settings ---
AUDIO_OUTPUT_FILENAME = "output_audio.mp3"
# Voices: https://github.com/rany2/edge-tts
VOICE_EN = "en-IN-PrabhatNeural" # Indian English
VOICE_HI = "hi-IN-MadhurNeural"  # Hindi
TTS_CHUNK_SIZE = 2000            # Characters per TTS chunk
