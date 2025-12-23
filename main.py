import os
import argparse
from src.pdf_extractor import extract_text_from_pdf
from src.tts_generator import generate_audio
from src.video_generator import generate_avatar_video
from src.utils import setup_logger
from src.config import DEFAULT_AVATAR_PATH

logger = setup_logger("Main")

def main():
    parser = argparse.ArgumentParser(description="Bhagwat Gita Narrator")
    parser.add_argument("--pdf_path", type=str, required=True, help="Path to the Bhagwat Gita PDF")
    parser.add_argument("--lang", type=str, default="en", choices=["en", "hi"], help="Language (en or hi)")
    parser.add_argument("--chapter", type=int, help="Specific chapter to process (optional)")
    parser.add_argument("--avatar_image", type=str, default=DEFAULT_AVATAR_PATH, help="Path to Krishna avatar image")
    parser.add_argument("--output", type=str, default="output_video.mp4", help="Output video filename")
    
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        logger.error(f"PDF file not found: {args.pdf_path}")
        return

    # 1. Extract Text
    logger.info(f"Extracting text from {args.pdf_path}...")
    text_data = extract_text_from_pdf(args.pdf_path, args.chapter)
    
    if not text_data:
        logger.error("No text found or failed to extract text.")
        return
        
    logger.info(f"Extracted {len(text_data)} characters.")

    # 2. Generate Audio
    logger.info(f"Generating audio in {args.lang}...")
    audio_path = generate_audio(text_data, args.lang)
    
    if not audio_path or not os.path.exists(audio_path):
        logger.error("Failed to generate audio.")
        return
        
    logger.info(f"Audio saved to {audio_path}")

    # 3. Generate Video
    logger.info(f"Generating video with Avatar to {args.output}...")
    temp_output = generate_avatar_video(audio_path, args.avatar_image)
    
    if temp_output and os.path.exists(temp_output):
        if temp_output != args.output:
            if os.path.exists(args.output):
                os.remove(args.output)
            os.rename(temp_output, args.output)
        logger.info(f"Video saved to {args.output}")
    else:
        logger.error("Failed to generate video.")

if __name__ == "__main__":
    main()
