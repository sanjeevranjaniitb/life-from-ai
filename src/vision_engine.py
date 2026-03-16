import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import logging

logger = logging.getLogger("VisionEngine")

class VisionEngine:
    def __init__(self):
        self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        logger.info(f"Loading Vision Model on {self.device}...")
        
        # Load to CPU first, then move to device. This is more stable for MPS.
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model.to(self.device)
        self.model.eval()
        logger.info("Vision Model Loaded.")

    def analyze_image(self, image_file):
        """
        Analyzes the image and returns a natural language description.
        """
        try:
            raw_image = Image.open(image_file).convert('RGB')
            
            # Prepare inputs
            inputs = self.processor(raw_image, return_tensors="pt").to(self.device)
            
            # Generate caption
            with torch.no_grad():
                # Some MPS ops can be unstable, running this part in a try-catch
                out = self.model.generate(**inputs, max_new_tokens=50)
            
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            
            # Clean up caption
            if caption.startswith("a woman is holding a camera"):
                return "you are taking a picture of me."
            
            return caption.capitalize() + "."
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            # Fallback to CPU if MPS fails
            if self.device == 'mps':
                logger.warning("Retrying vision analysis on CPU...")
                try:
                    self.model.to('cpu')
                    inputs = self.processor(raw_image, return_tensors="pt").to('cpu')
                    with torch.no_grad():
                        out = self.model.generate(**inputs, max_new_tokens=50)
                    caption = self.processor.decode(out[0], skip_special_tokens=True)
                    self.model.to('mps') # Move back to MPS for next time
                    return caption.capitalize() + "."
                except Exception as cpu_e:
                    logger.error(f"CPU fallback also failed: {cpu_e}")

            return "I couldn't quite see what that was."
