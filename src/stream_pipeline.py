import threading
import queue
import re
import os
import time
import cv2
import sys
import subprocess
from src.tts_generator import generate_audio
from src.config import WAV2LIP_DIR, WAV2LIP_CHECKPOINT, WAV2LIP_INFERENCE_SCRIPT

class StreamPipeline:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.video_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.active_thread = None

    def start(self, text, avatar_path):
        """Starts the generation thread."""
        self.stop_event.clear()
        
        # Clear queue
        while not self.video_queue.empty():
            try: self.video_queue.get_nowait()
            except: pass
            
        self.active_thread = threading.Thread(
            target=self._worker, 
            args=(text, avatar_path, self.video_queue, self.output_dir, self.stop_event)
        )
        self.active_thread.daemon = True
        self.active_thread.start()

    @staticmethod
    def _worker(full_text, avatar_path, video_queue, output_dir, stop_event):
        # 1. Chunk Text by punctuation for natural breaks
        # Smaller chunks = faster start, but more pauses
        parts = re.split(r'([,.;?!])', full_text)
        chunks = []
        current = ""
        for p in parts:
            current += p
            if len(current) > 20 or p in ",.;?!": # Chunk every ~4-5 words
                if current.strip(): chunks.append(current.strip())
                current = ""
        if current.strip(): chunks.append(current.strip())
        
        # 2. Process
        for i, chunk in enumerate(chunks):
            if stop_event.is_set(): break
            
            # Paths
            audio_path = os.path.join(output_dir, f"chunk_{i}.mp3")
            video_path = os.path.join(output_dir, f"chunk_{i}.mp4")
            
            # TTS
            gen_audio = generate_audio(chunk)
            if gen_audio:
                if os.path.exists(audio_path): os.remove(audio_path)
                os.rename(gen_audio, audio_path)
                
                # Real Wav2Lip Generation
                success = StreamPipeline._run_wav2lip(audio_path, avatar_path, video_path)
                
                if success:
                    video_queue.put(video_path)
        
        video_queue.put(None) # End

    @staticmethod
    def _run_wav2lip(audio_path, avatar_path, output_path):
        try:
            # Resize 128x128 for speed (Balance)
            temp_face = output_path.replace(".mp4", "_face.jpg")
            img = cv2.imread(avatar_path)
            cv2.imwrite(temp_face, cv2.resize(img, (128, 128)))

            command = [
                sys.executable, WAV2LIP_INFERENCE_SCRIPT,
                "--checkpoint_path", WAV2LIP_CHECKPOINT,
                "--face", temp_face,
                "--audio", audio_path,
                "--outfile", output_path,
                "--resize_factor", "1", 
                "--nosmooth",
                "--wav2lip_batch_size", "8" # Batch size 8 for 128p on MPS
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = WAV2LIP_DIR
            
            subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(temp_face): os.remove(temp_face)
            return os.path.exists(output_path)
        except:
            return False

    def get_next_video(self):
        try:
            return self.video_queue.get_nowait()
        except queue.Empty:
            return "WAIT"
