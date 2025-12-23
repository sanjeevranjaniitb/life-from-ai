import pdfplumber
import re
import logging

logger = logging.getLogger("PDFExtractor")

def extract_text_from_pdf(pdf_path: str, chapter_number: int = None) -> str:
    """
    Extracts text from a PDF file, optionally filtering by chapter number.
    
    Args:
        pdf_path (str): Path to the PDF file.
        chapter_number (int, optional): The chapter number to extract.

    Returns:
        str: The extracted text, or None if extraction failed.
    """
    full_text = _read_pdf_content(pdf_path)
    if not full_text:
        return None

    cleaned_text = _clean_text(full_text)

    if chapter_number is None:
        return cleaned_text

    return _extract_chapter(cleaned_text, chapter_number)

def _read_pdf_content(pdf_path: str) -> str:
    """Reads raw text content from the PDF."""
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"Opened PDF with {len(pdf.pages)} pages.")
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return "\n".join(text_content)
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return None

def _clean_text(text: str) -> str:
    """Cleans the extracted text by removing hyphenation and normalizing spaces."""
    # Remove hyphenation at end of lines (e.g. "exam-\nple" -> "example")
    text = re.sub(r'-\n', '', text)
    
    # Normalize newlines: 
    # Replace single newlines with space (unwrapping hard wrapped text)
    # Keep double newlines as paragraph breaks.
    text = text.replace('\n\n', '||PARAGRAPH||')
    text = text.replace('\n', ' ')
    text = text.replace('||PARAGRAPH||', '\n')
    
    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def _extract_chapter(text: str, chapter_number: int) -> str:
    """Extracts a specific chapter from the full text using heuristics."""
    logger.info(f"Attempting to extract Chapter {chapter_number}...")
    
    # Patterns to find Chapter headers
    chapter_patterns = [
        f"Chapter {chapter_number}", f"CHAPTER {chapter_number}",
        f"Adhyay {chapter_number}", f"ADHYAY {chapter_number}"
    ]
    
    start_index = _find_pattern_index(text, chapter_patterns)
    
    if start_index == -1:
        logger.warning(f"Could not find start of Chapter {chapter_number}. Returning full text.")
        return text

    # Find end of chapter (start of next chapter)
    next_chapter_num = chapter_number + 1
    next_chapter_patterns = [
        f"Chapter {next_chapter_num}", f"CHAPTER {next_chapter_num}",
        f"Adhyay {next_chapter_num}", f"ADHYAY {next_chapter_num}"
    ]
    
    end_index = _find_pattern_index(text, next_chapter_patterns, start_index + 100)
    
    if end_index != -1:
        logger.info(f"Extracted Chapter {chapter_number} successfully.")
        return text[start_index:end_index].strip()
    
    return text[start_index:].strip()

def _find_pattern_index(text: str, patterns: list, start_search_from: int = 0) -> int:
    """Helper to find the first occurrence of any pattern in the list."""
    for pattern in patterns:
        idx = text.find(pattern, start_search_from)
        if idx != -1:
            return idx
    return -1
