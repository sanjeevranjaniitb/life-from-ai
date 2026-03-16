import os
import cv2
import subprocess
import sys
import numpy as np
import wave
from src.config import WAV2LIP_DIR, WAV2LIP_CHECKPOINT, WAV2LIP_INFERENCE_SCRIPT

def generate_talking_loop(avatar_path, output_path):
    """
    Generates a talking loop and extracts its first frame for a seamless UI.
    """
    if not os.path.exists(avatar_path): return None, None
    
    # Paths
    temp_dir = "temp/loop_gen"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    # 1. Resize Input to a consistent size (512x512)
    # This ensures Wav2Lip has a decent canvas to work with
    img_hd = cv2.imread(avatar_path)
    img_hd = cv2.resize(img_hd, (512, 512), interpolation=cv2.INTER_AREA)
    temp_face = os.path.join(temp_dir, "input_face.jpg")
    cv2.imwrite(temp_face, img_hd)
    
    # 2. Create Dummy Audio
    dummy_audio = os.path.join(temp_dir, "driver.wav")
    with wave.open(dummy_audio, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        data = np.random.uniform(-0.5, 0.5, 16000 * 2) 
        f.writeframes((data * 32767).astype(np.int16).tobytes())

    # 3. Run Wav2Lip
    try:
        command = [
            sys.executable, WAV2LIP_INFERENCE_SCRIPT,
            "--checkpoint_path", WAV2LIP_CHECKPOINT,
            "--face", temp_face,
            "--audio", dummy_audio,
            "--outfile", output_path,
            "--resize_factor", "1",
            "--nosmooth"
        ]
        
        env = os.environ.copy()
        env["PYTHONPATH"] = WAV2LIP_DIR
        env["OMP_NUM_THREADS"] = "1"
        
        subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if not os.path.exists(output_path): return None, None
        
        # 4. Extract First Frame (Crucial for Seamless UI)
        cap = cv2.VideoCapture(output_path)
        ret, frame = cap.read()
        cap.release()
        
        static_frame_path = output_path.replace(".mp4", "_idle.jpg")
        if ret:
            cv2.imwrite(static_frame_path, frame)
            return output_path, static_frame_path
            
    except Exception as e:
        print(f"Loop generation failed: {e}")
        return None, None
        
    return None, None
