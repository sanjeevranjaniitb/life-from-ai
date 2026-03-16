import os
import time
import sys
import cv2
import logging

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tts_generator import generate_audio
from src.config import WAV2LIP_DIR, WAV2LIP_CHECKPOINT, WAV2LIP_INFERENCE_SCRIPT

# Setup logging
logging.basicConfig(filename='worker.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("Worker")

# Paths
QUEUE_FILE = "temp/job_queue.txt"
PLAYLIST_FILE = "temp/playlist.txt"
AVATAR_PATH = "assets/custom.jpg"
DEFAULT_AVATAR = "assets/krishna.jpg"

def run_wav2lip(audio_path, output_path):
    """Runs Wav2Lip subprocess."""
    try:
        # Resize avatar for speed (96x96 is NATIVE Wav2Lip resolution = Fastest)
        target_avatar = AVATAR_PATH if os.path.exists(AVATAR_PATH) else DEFAULT_AVATAR
        
        img = cv2.imread(target_avatar)
        if img is None: 
            logger.error(f"Could not read avatar at {target_avatar}")
            return False
        
        temp_face = output_path.replace(".mp4", "_face.jpg")
        cv2.imwrite(temp_face, cv2.resize(img, (96, 96)))

        command = [
            sys.executable, WAV2LIP_INFERENCE_SCRIPT,
            "--checkpoint_path", WAV2LIP_CHECKPOINT,
            "--face", temp_face,
            "--audio", audio_path,
            "--outfile", output_path,
            "--resize_factor", "1", 
            "--nosmooth",
            "--wav2lip_batch_size", "8" # Try larger batch for 96x96
        ]
        
        env = os.environ.copy()
        env["PYTHONPATH"] = WAV2LIP_DIR
        env["OMP_NUM_THREADS"] = "2" # Allow 2 threads for slightly better throughput
        
        import subprocess
        subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(temp_face): os.remove(temp_face)
        return os.path.exists(output_path)
    except Exception as e:
        logger.error(f"Wav2Lip Failed: {e}")
        return False

def main():
    logger.info("Worker started. Waiting for jobs...")
    
    # Ensure files exist
    if not os.path.exists("temp"): os.makedirs("temp")
    if not os.path.exists(QUEUE_FILE): open(QUEUE_FILE, 'w').close()
    
    while True:
        try:
            # Read first line of queue
            with open(QUEUE_FILE, 'r') as f:
                lines = f.readlines()
                
            if not lines:
                time.sleep(0.5)
                continue
                
            # Pop first item
            current_job = lines[0].strip()
            
            # Rewrite queue without first item
            with open(QUEUE_FILE, 'w') as f:
                f.writelines(lines[1:])
                
            if not current_job: continue
            
            # Process Job: "ID|TEXT"
            job_id, text = current_job.split('|', 1)
            logger.info(f"Processing chunk {job_id}...")
            
            # 1. TTS
            if not os.path.exists("outputs"): os.makedirs("outputs")
            audio_path = f"outputs/{job_id}.mp3"
            video_path = f"outputs/{job_id}.mp4"
            
            # Cleanup old
            if os.path.exists(audio_path): os.remove(audio_path)
            if os.path.exists(video_path): os.remove(video_path)
            
            gen_audio = generate_audio(text)
            
            if gen_audio:
                # Move to outputs
                if os.path.exists(audio_path): os.remove(audio_path)
                os.rename(gen_audio, audio_path)
                
                # 2. Wav2Lip
                if run_wav2lip(audio_path, video_path):
                    # 3. Add to Playlist
                    with open(PLAYLIST_FILE, 'a') as f:
                        f.write(f"{video_path}\n")
                    logger.info(f"Chunk {job_id} ready.")
                else:
                    logger.error("Video generation failed.")
            else:
                logger.error("TTS failed.")
                
        except Exception as e:
            logger.error(f"Job loop error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
