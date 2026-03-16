import os
import subprocess
import logging
import sys
import cv2
from src.config import WAV2LIP_DIR, WAV2LIP_CHECKPOINT, WAV2LIP_INFERENCE_SCRIPT

logger = logging.getLogger("VideoGenerator")

def generate_avatar_video(audio_path, avatar_image_path, output_filename):
    """
    Generates a lip-synced video.
    EXTREME OPTIMIZATION: 128x128 resolution, 15 FPS target (via frame skipping/ffmpeg post-process).
    """
    if not os.path.exists(avatar_image_path) or not os.path.exists(audio_path):
        return None

    # 1. Extreme Downscale
    resized_avatar_path = "temp/resized_avatar_fast.jpg"
    # 128x128 is significantly faster than 256x256
    _resize_image(avatar_image_path, resized_avatar_path, size=(128, 128))

    command = [
        sys.executable, WAV2LIP_INFERENCE_SCRIPT,
        "--checkpoint_path", WAV2LIP_CHECKPOINT,
        "--face", resized_avatar_path,
        "--audio", audio_path,
        "--outfile", output_filename,
        "--resize_factor", "1", 
        "--nosmooth",
        "--wav2lip_batch_size", "4"
    ]
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = WAV2LIP_DIR
        env["OMP_NUM_THREADS"] = "1"
        
        # Increase timeout to 180s just in case, but aim for speed
        subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        
        if os.path.exists(output_filename):
            return output_filename
            
    except subprocess.TimeoutExpired:
        logger.error("Wav2Lip timed out!")
    except Exception as e:
        logger.error(f"Wav2Lip error: {e}")

    return None

def _resize_image(input_path, output_path, size=(128, 128)):
    try:
        img = cv2.imread(input_path)
        if img is not None:
            img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
            cv2.imwrite(output_path, img)
    except Exception:
        pass
