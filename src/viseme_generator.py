import os
import cv2
import sys
import torch
import numpy as np
from src.config import WAV2LIP_DIR, WAV2LIP_CHECKPOINT

# Add Wav2Lip to path
sys.path.append(WAV2LIP_DIR)
from models import Wav2Lip
import face_detection

class VisemeGenerator:
    def __init__(self):
        # Force CPU for face detection (MPS crash workaround)
        self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, flip_input=False, device='cpu')
        self.model = self._load_model(WAV2LIP_CHECKPOINT)

    def _load_model(self, path):
        model = Wav2Lip()
        # Load checkpoint to CPU first
        checkpoint = torch.load(path, map_location='cpu')
        s = checkpoint["state_dict"]
        new_s = {k.replace('module.', ''): v for k, v in s.items()}
        model.load_state_dict(new_s)
        model = model.to(self.device)
        return model.eval()

    def generate_visemes(self, avatar_path, output_dir="temp/visemes"):
        """
        Generates a bank of key viseme images from a source avatar.
        This is a one-time process per avatar.
        """
        if not os.path.exists(avatar_path):
            return None
        os.makedirs(output_dir, exist_ok=True)

        # Define phonemes and their corresponding audio energy patterns (mel chunks)
        # Wav2Lip mel chunks are (80, 16) before batching
        viseme_definitions = {
            'a': np.ones((80, 16)) * 2.5,                               # Loud 'Ah'
            'e': self._create_mel_pattern(high_freq=True),              # 'Ee', 'S'
            'o': self._create_mel_pattern(low_freq=True),               # 'Oh', 'Oo'
            'm': np.ones((80, 16)) * -4.0,                              # Closed lips for M, B, P
        }

        # The 'idle' state should just be the perfect, untouched original image.
        original_frame = cv2.imread(avatar_path)
        if original_frame is None:
            return None
            
        cv2.imwrite(os.path.join(output_dir, "idle.jpg"), original_frame)

        # Generate and save each active viseme
        for name, mel_chunk in viseme_definitions.items():
            generated_frame = self._generate_frame(original_frame, mel_chunk)
            cv2.imwrite(os.path.join(output_dir, f"{name}.jpg"), generated_frame)
        
        return output_dir

    def _create_mel_pattern(self, low_freq=False, high_freq=False):
        mel = np.zeros((80, 16))
        if low_freq:
            mel[:25, :] = 3.0  # Energy in lower frequencies
        if high_freq:
            mel[55:, :] = 3.0  # Energy in higher frequencies
        return mel

    def _generate_frame(self, frame, mel_chunk):
        """Internal function to run Wav2Lip for a single frame."""
        # Detect face in the original frame (using RGB for accuracy)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.detector.get_detections_for_batch(np.array([frame_rgb]))
        if not faces or faces[0] is None:
            return frame

        x1, y1, x2, y2 = faces[0]
        
        # Padding adjustments matching Wav2Lip inference.py
        pady1, pady2, padx1, padx2 = [0, 10, 0, 0]
        
        h, w = frame.shape[:2]
        x1 = max(0, int(x1) - padx1)
        y1 = max(0, int(y1) - pady1)
        x2 = min(w, int(x2) + padx2)
        y2 = min(h, int(y2) + pady2)
        
        if x2 <= x1 or y2 <= y1:
            return frame

        # Extract face region
        face_roi = frame[y1:y2, x1:x2]

        # Prepare image for Wav2Lip (96x96)
        face_resized = cv2.resize(face_roi, (96, 96))
        
        # Convert to numpy array list format expected by datagen logic
        img_batch = [face_resized]
        mel_batch = [mel_chunk]

        img_batch = np.asarray(img_batch)
        mel_batch = np.asarray(mel_batch)

        # Create masked image
        img_masked = img_batch.copy()
        img_masked[:, 96//2:] = 0

        # Concatenate and normalize
        img_concat = np.concatenate((img_masked, img_batch), axis=3) / 255.0
        
        # Reshape Mel to (Batch, 80, 16, 1)
        mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

        # Transpose to (Batch, Channels, H, W)
        img_tensor = torch.FloatTensor(np.transpose(img_concat, (0, 3, 1, 2))).to(self.device)
        mel_tensor = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(self.device)

        # Run inference
        with torch.no_grad():
            pred = self.model(mel_tensor, img_tensor)

        # Process output
        pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.0
        pred_img_rgb = pred[0].astype(np.uint8)
        
        # Convert back to BGR for OpenCV
        pred_img_bgr = cv2.cvtColor(pred_img_rgb, cv2.COLOR_RGB2BGR)

        # Upscale generated patch
        target_h = y2 - y1
        target_w = x2 - x1
        pred_high_res_bgr = cv2.resize(pred_img_bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        
        # --- ULTIMATE FIX: POISSON SEAMLESS CLONING ---
        # This algorithm literally dissolves the boundary between the two images.
        
        # 1. Create a binary mask defining the region we want to paste (the mouth).
        # We make it an oval shape covering the lower half of the face ROI.
        mask = np.zeros(pred_high_res_bgr.shape, pred_high_res_bgr.dtype)
        
        # Define the center and axes of the ellipse mask
        # Center is horizontally middle, vertically slightly below the middle (where the mouth is)
        center_x = target_w // 2
        center_y = int(target_h * 0.75) 
        axes_x = int(target_w * 0.45) # width of the mask
        axes_y = int(target_h * 0.25) # height of the mask
        
        # Draw a solid white ellipse on the black mask
        cv2.ellipse(mask, (center_x, center_y), (axes_x, axes_y), 0, 0, 360, (255, 255, 255), -1)

        # 2. Define where the center of the source image will be placed in the destination image
        # Since pred_high_res_bgr is exactly the size of face_roi, the center is just the offset
        paste_center = (x1 + center_x, y1 + center_y)

        # 3. Apply Seamless Cloning
        # cv2.NORMAL_CLONE preserves the source texture (teeth/lips) while matching the destination's boundary colors.
        try:
            final_frame = cv2.seamlessClone(pred_high_res_bgr, frame, mask, paste_center, cv2.NORMAL_CLONE)
        except cv2.error as e:
            # Fallback just in case the mask goes out of bounds (highly unlikely with this setup)
            print(f"Seamless clone failed, falling back to alpha blend: {e}")
            final_frame = frame.copy()
            # Simple fallback if cloning fails
            final_frame[y1:y2, x1:x2] = pred_high_res_bgr

        return final_frame
