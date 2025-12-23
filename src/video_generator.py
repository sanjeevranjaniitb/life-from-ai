import os
import subprocess
import logging
import sys
import librosa
import math
from src.config import WAV2LIP_DIR, WAV2LIP_CHECKPOINT, WAV2LIP_INFERENCE_SCRIPT

logger = logging.getLogger("VideoGenerator")

def generate_avatar_video(audio_path: str, avatar_image_path: str) -> str:
    """
    Generates a video with the avatar lip-syncing to the audio.
    Adds a 'breathing' camera effect to make the static image look alive.
    
    Args:
        audio_path (str): Path to the audio file.
        avatar_image_path (str): Path to the avatar image.

    Returns:
        str: Path to the generated video file, or None if failed.
    """
    output_video = "output_video.mp4"
    
    if not _validate_inputs(audio_path, avatar_image_path):
        return None

    if not os.path.exists(WAV2LIP_DIR):
        logger.warning("Wav2Lip not found. Falling back to static image.")
        return _generate_static_video(audio_path, avatar_image_path, output_video)

    # 1. Create an "Alive" video input (Zoom/Pan) instead of static image
    # This makes the avatar look like it's breathing/moving slightly.
    alive_video_path = "temp_alive_input.mp4"
    if _create_alive_video(avatar_image_path, audio_path, alive_video_path):
        # Use the animated video as input
        face_input = alive_video_path
    else:
        # Fallback to static image if animation fails
        face_input = avatar_image_path

    # 2. Run Wav2Lip
    result = _run_wav2lip(audio_path, face_input, output_video)
    
    # Cleanup
    if os.path.exists(alive_video_path):
        os.remove(alive_video_path)
        
    return result

def _validate_inputs(audio_path, avatar_image_path):
    if not os.path.exists(avatar_image_path):
        logger.error(f"Avatar image not found at {avatar_image_path}.")
        return False
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found at {audio_path}.")
        return False
    return True

def _create_alive_video(image_path, audio_path, output_path):
    """
    Creates a video from the static image with a more pronounced 'breathing' effect.
    Uses a sine wave function for zoom to simulate inhalation/exhalation.
    """
    try:
        logger.info("Applying 'Alive' effect (Sine Wave Breathing)...")
        
        # Get audio duration
        duration = librosa.get_duration(filename=audio_path)
        duration += 1.0 
        
        # FFMPEG Complex Filter for "Breathing"
        # We use the 'zoompan' filter but with a sine wave expression for the zoom factor.
        # z='min(zoom+0.0015,1.5)' was linear.
        # New expression: 1.05 + 0.03*sin(2*PI*on/100)
        # This creates a rhythmic zoom in and out (breathing) every ~4 seconds (assuming 25fps)
        
        # Parameters:
        # d=1: Duration of each frame (we want smooth transition so we rely on the expression)
        # But zoompan works by creating a sequence.
        # Let's try a simpler approach that is robust: A slow, continuous zoom in, then a pan.
        # Or a sine wave zoom.
        
        # Expression: 1.02 + 0.02 * sin(time * 1.5)
        # time is available in some filters, but zoompan uses frame numbers (in/on).
        # on = output frame number.
        # 25 fps. 1 cycle every 4 seconds = 100 frames.
        # sin(2 * 3.14159 * on / 100)
        
        # We also add a slight pan to make it feel handheld.
        # x='iw/2-(iw/zoom/2) + 2*sin(2*3.14*on/200)'
        
        zoom_expr = "1.05+0.02*sin(2*3.14*on/150)" # Breathing zoom
        x_expr = "iw/2-(iw/zoom/2)+2*sin(2*3.14*on/250)" # Subtle horizontal sway
        y_expr = "ih/2-(ih/zoom/2)+1*cos(2*3.14*on/250)" # Subtle vertical sway
        
        command = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d=1:s=1280x720:fps=25",
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        # Suppress output unless error
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
        
    except Exception as e:
        logger.warning(f"Failed to create alive video: {e}. Using static image.")
        return False

def _run_wav2lip(audio_path, face_input, output_video):
    """Runs the Wav2Lip inference script."""
    logger.info("Generating realistic lip-sync video using Wav2Lip...")
    
    command = [
        sys.executable, WAV2LIP_INFERENCE_SCRIPT,
        "--checkpoint_path", WAV2LIP_CHECKPOINT,
        "--face", face_input,
        "--audio", audio_path,
        "--outfile", output_video,
        "--resize_factor", "1",
        "--nosmooth"
    ]
    
    try:
        # Set PYTHONPATH to include Wav2Lip directory so it can find its modules
        env = os.environ.copy()
        env["PYTHONPATH"] = WAV2LIP_DIR
        
        logger.info("Running Wav2Lip inference...")
        subprocess.run(command, check=True, env=env)
        
        if os.path.exists(output_video):
            logger.info(f"Lip-sync video generated successfully: {output_video}")
            return output_video
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Wav2Lip failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    return None

def _generate_static_video(audio_path, avatar_image_path, output_video):
    """Fallback: Generates a static video using FFMPEG."""
    logger.info("Generating static video using FFMPEG (Fallback)...")
    command = [
        "ffmpeg", "-y", "-loop", "1", "-i", avatar_image_path, "-i", audio_path,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest", output_video
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_video
    except Exception as e:
        logger.error(f"FFMPEG fallback failed: {e}")
        return None
