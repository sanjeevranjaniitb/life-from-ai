import asyncio
import edge_tts
import os
from tqdm import tqdm
from src.config import VOICE_EN, VOICE_HI, TTS_CHUNK_SIZE, AUDIO_OUTPUT_FILENAME

async def _generate_audio_chunk(text, voice, output_file):
    """Generates a single audio chunk."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

async def _combine_audio_chunks(chunks, output_file):
    """Combines multiple audio chunks into one file using FFMPEG."""
    list_file = "chunks.txt"
    try:
        with open(list_file, "w") as f:
            for chunk in chunks:
                # Escape single quotes in filenames for ffmpeg
                safe_chunk = chunk.replace("'", "'\\''")
                f.write(f"file '{safe_chunk}'\n")
                
        # ffmpeg concat demuxer
        command = f"ffmpeg -y -f concat -safe 0 -i {list_file} -c copy {output_file} -loglevel error"
        os.system(command)
    finally:
        # Cleanup
        if os.path.exists(list_file):
            os.remove(list_file)
        for chunk in chunks:
            if os.path.exists(chunk):
                os.remove(chunk)

def generate_audio(text: str, lang: str = "en") -> str:
    """
    Generates audio from text using edge-tts.
    Handles long text by chunking it into smaller pieces.
    
    Args:
        text (str): The text to convert to speech.
        lang (str): Language code ('en' or 'hi').

    Returns:
        str: Path to the generated audio file.
    """
    voice = VOICE_HI if lang == "hi" else VOICE_EN
    output_file = AUDIO_OUTPUT_FILENAME

    # Split text into chunks to avoid timeouts
    chunks = [text[i:i+TTS_CHUNK_SIZE] for i in range(0, len(text), TTS_CHUNK_SIZE)]
    audio_chunks = []
    
    try:
        print(f"Generating audio in {len(chunks)} chunks...")
        for i, chunk in enumerate(tqdm(chunks, desc="TTS Progress")):
            chunk_file = f"chunk_{i}.mp3"
            asyncio.run(_generate_audio_chunk(chunk, voice, chunk_file))
            audio_chunks.append(chunk_file)
            
        if len(audio_chunks) == 1:
            if os.path.exists(output_file):
                os.remove(output_file)
            os.rename(audio_chunks[0], output_file)
        else:
            print("Combining audio chunks...")
            asyncio.run(_combine_audio_chunks(audio_chunks, output_file))
            
        return output_file

    except Exception as e:
        print(f"Error generating TTS: {e}")
        # Cleanup on failure
        for chunk in audio_chunks:
            if os.path.exists(chunk):
                os.remove(chunk)
        return None
