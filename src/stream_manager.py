import os
import re
import queue
import threading
import time
from pydub import AudioSegment
from src.tts_generator import generate_audio

class StreamManager:
    def __init__(self, wav2lip_instance, output_dir="outputs"):
        self.output_dir = output_dir
        self.wav2lip = wav2lip_instance
        os.makedirs(output_dir, exist_ok=True)
        self.video_queue = queue.Queue()
        self.stop_event = threading.Event()

    def start_generation(self, full_text, avatar_path):
        self.stop_event.clear()
        # Clear queue
        while not self.video_queue.empty():
            try: self.video_queue.get_nowait()
            except: pass
            
        thread = threading.Thread(target=self._generation_worker, args=(full_text, avatar_path))
        thread.daemon = True
        thread.start()

    def _generation_worker(self, full_text, avatar_path):
        # 1. Smart Splitting (Phrases)
        # Split by punctuation but keep it
        raw_phrases = re.split(r'([,.;?!])', full_text)
        phrases = []
        current = ""
        
        for part in raw_phrases:
            current += part
            # Chunk if punctuation or length > 60 chars
            if re.match(r'[,.;?!]', part) or len(current) > 60:
                if current.strip():
                    phrases.append(current.strip())
                current = ""
        if current.strip():
            phrases.append(current.strip())
            
        # 2. Loop
        for i, phrase in enumerate(phrases):
            if self.stop_event.is_set(): break
            
            # Paths
            audio_path = os.path.join(self.output_dir, f"chunk_{i}.mp3")
            video_temp = os.path.join(self.output_dir, f"temp_{i}.mp4")
            
            # Generate Audio
            gen_audio = generate_audio(phrase)
            if gen_audio:
                if os.path.exists(audio_path): os.remove(audio_path)
                os.rename(gen_audio, audio_path)
                
                # Duration
                duration = 0
                try:
                    sound = AudioSegment.from_mp3(audio_path)
                    duration = sound.duration_seconds
                except: pass

                # IN-MEMORY GENERATION (Fast!)
                final_video = self.wav2lip.generate_video_file(avatar_path, audio_path, video_temp)
                
                if final_video:
                    self.video_queue.put({
                        "video_path": final_video,
                        "duration": duration,
                        "text": phrase
                    })
        
        self.video_queue.put(None)

    def get_next_chunk(self):
        return self.video_queue.get()
