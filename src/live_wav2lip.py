import torch
import numpy as np
import cv2
import os
import sys
import subprocess
from src.config import BASE_DIR

# Add Wav2Lip to path
WAV2LIP_PATH = os.path.join(BASE_DIR, "Wav2Lip")
sys.path.append(WAV2LIP_PATH)

from Wav2Lip.models import Wav2Lip
import Wav2Lip.audio as audio
import face_detection

class LiveWav2Lip:
    def __init__(self, checkpoint_path, device='cpu'):
        self.device = device
        self.model = self._load_model(checkpoint_path)
        self.face_detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, 
                                                           flip_input=False, device=device)
        self.img_size = 96
        self.mel_step_size = 16
        self.fps = 25

    def _load_model(self, path):
        model = Wav2Lip()
        checkpoint = torch.load(path, map_location=lambda storage, loc: storage)
        s = checkpoint["state_dict"]
        new_s = {}
        for k, v in s.items():
            new_s[k.replace('module.', '')] = v
        model.load_state_dict(new_s)
        model = model.to(self.device)
        return model.eval()

    def generate_video_file(self, face_image_path, audio_path, output_path):
        """
        Generates a video file using the loaded model and OpenCV Writer.
        This is MUCH faster than calling inference.py via subprocess.
        """
        # 1. Load Resources
        original_frame = cv2.imread(face_image_path)
        if original_frame is None: return None
        
        # Detect Face (Once per chunk)
        faces = self.face_detector.get_detections_for_batch(np.array([original_frame]))
        if not faces or faces[0] is None: return None
        x1, y1, x2, y2 = faces[0]
        
        # Audio
        wav = audio.load_wav(audio_path, 16000)
        mel = audio.melspectrogram(wav)
        
        # 2. Setup Video Writer (OpenCV)
        height, width, _ = original_frame.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
        
        # 3. Batch Process
        mel_chunks = []
        mel_idx_multiplier = 80./self.fps
        i = 0
        while True:
            start_idx = int(i * mel_idx_multiplier)
            if start_idx + self.mel_step_size > len(mel[0]): break
            mel_chunks.append(mel[:, start_idx : start_idx + self.mel_step_size])
            i += 1

        # Prepare Face
        face_roi = original_frame[y1:y2, x1:x2]
        face_low_res = cv2.resize(face_roi, (self.img_size, self.img_size))
        
        # Mask
        face_masked = face_low_res.copy()
        face_masked[self.img_size//2:, :] = 0
        
        # Input Tensor
        img_batch = np.concatenate((face_masked, face_low_res), axis=2)
        img_batch = np.array([img_batch], dtype=np.float32) / 255.
        img_batch = np.transpose(img_batch, (0, 3, 1, 2))
        img_batch = torch.FloatTensor(img_batch).to(self.device)

        # 4. Inference Loop
        # Process in batches of 8 for speed
        batch_size = 8
        
        for idx in range(0, len(mel_chunks), batch_size):
            batch_mels = mel_chunks[idx : idx + batch_size]
            
            # Prepare Audio Batch
            mel_batch = []
            for m in batch_mels:
                m = np.reshape(m, [1, m.shape[0], m.shape[1], 1])
                m = np.transpose(m, (0, 3, 1, 2))
                mel_batch.append(m)
            
            if not mel_batch: break
            
            mel_batch = np.concatenate(mel_batch, axis=0)
            mel_batch = torch.FloatTensor(mel_batch).to(self.device)
            
            # Repeat face to match audio batch
            current_batch_size = len(batch_mels)
            img_batch_repeated = img_batch.repeat(current_batch_size, 1, 1, 1)

            with torch.no_grad():
                pred = self.model(mel_batch, img_batch_repeated)

            # 5. Reconstruct Frames
            pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.
            
            for p in pred:
                # Upscale mouth
                p_high = cv2.resize(p.astype(np.uint8), (x2-x1, y2-y1))
                
                # Paste
                final_frame = original_frame.copy()
                final_frame[y1:y2, x1:x2] = p_high
                
                out.write(final_frame)
                
        out.release()
        
        # 6. Mux Audio (Fastest way is still ffmpeg copy)
        # OpenCV writer doesn't write audio. We merge them quickly.
        final_output = output_path.replace(".mp4", "_audio.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", output_path, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            final_output
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return final_output
