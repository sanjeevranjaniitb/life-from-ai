import cv2
import numpy as np
import os

class MorphEngine:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Define Viseme Shapes (Open Ratio, Width Ratio)
        # 0.0 = Natural, + = Open/Wide, - = Closed/Narrow
        self.viseme_map = {
            'idle': (0.0, 0.0),
            'ah': (0.25, 0.0),   # A, H, R
            'ee': (0.05, 0.2),   # E, I, S, Z
            'oo': (0.15, -0.15), # O, U, W, Q
            'mm': (-0.05, 0.0),  # M, B, P, F, V
            'th': (0.1, 0.0)     # T, D, N, K, G
        }

    def get_shape_for_char(self, char):
        char = char.lower()
        if char in "aeh": return self.viseme_map['ah']
        if char in "iyjzxsv": return self.viseme_map['ee']
        if char in "ouqw": return self.viseme_map['oo']
        if char in "mbpfv": return self.viseme_map['mm']
        if char in "tdnkg": return self.viseme_map['th']
        if char in " .,?!": return self.viseme_map['idle']
        return self.viseme_map['ah'] # Default to slight open for consonants

    def generate_viseme_bank(self, image_path, output_dir="temp/visemes"):
        """Pre-generates warped frames for all key visemes."""
        if not os.path.exists(image_path): return
        os.makedirs(output_dir, exist_ok=True)
        img = cv2.imread(image_path)
        if img is None: return

        # Detect Face once
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rects = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(rects) == 0: return # Needs face
        x, y, w, h = rects[0]

        # Generate all states
        for name, (open_r, width_r) in self.viseme_map.items():
            warped = self._warp_mouth(img, x, y, w, h, open_r, width_r)
            cv2.imwrite(os.path.join(output_dir, f"{name}.jpg"), warped)
            
        return output_dir

    def _warp_mouth(self, img, x, y, w, h, open_ratio, width_ratio):
        result = img.copy()
        mouth_y = int(y + 2 * h / 3)
        mouth_h = int(h / 3)
        mouth_x = int(x + w / 4)
        mouth_w = int(w / 2)
        
        jaw_roi = img[mouth_y:mouth_y+mouth_h, mouth_x:mouth_x+mouth_w]
        
        # Vertical Shift
        shift_y = int(mouth_h * open_ratio)
        
        # Horizontal Stretch
        new_width = int(mouth_w * (1.0 + width_ratio))
        if new_width < 1: new_width = 1
        
        # Draw Oral Cavity
        cv2.ellipse(result, 
                   (mouth_x + mouth_w//2, mouth_y + mouth_h//3), 
                   (mouth_w//3, int(abs(shift_y) * 1.5) + 5), 
                   0, 0, 360, (20, 15, 30), -1)
        
        # Resize Jaw
        jaw_resized = cv2.resize(jaw_roi, (new_width, mouth_h))
        offset_x = (mouth_w - new_width) // 2
        
        # Paste
        paste_y = mouth_y + shift_y
        paste_x = mouth_x + offset_x
        
        h_src, w_src, _ = jaw_resized.shape
        h_dst, w_dst, _ = result.shape
        
        if paste_y + h_src > h_dst: h_src = h_dst - paste_y
        if paste_x + w_src > w_dst: w_src = w_dst - paste_x
        if paste_x < 0: 
            w_src += paste_x
            paste_x = 0
            
        if h_src > 0 and w_src > 0:
            result[paste_y:paste_y+h_src, paste_x:paste_x+w_src] = jaw_resized[:h_src, :w_src]
            
        return result
