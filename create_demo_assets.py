import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw
import requests

def download_font(font_name, url):
    """Downloads a font file if it doesn't exist."""
    if not os.path.exists(font_name):
        print(f"Downloading font: {font_name}...")
        response = requests.get(url)
        with open(font_name, 'wb') as f:
            f.write(response.content)

def create_demo_pdf(filename="gita_demo.pdf"):
    """Creates a dummy PDF with Bhagwat Gita content for testing."""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title Page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height / 2, "Bhagwat Gita Demo")
    c.showPage()

    # Chapter 1
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Chapter 1")
    c.setFont("Helvetica", 12)
    
    text = """
    Dhrtarastra said: O Sanjaya, after my sons and the sons of Pandu assembled in the place of pilgrimage at Kuruksetra, desiring to fight, what did they do?
    
    Sanjaya said: O King, after looking over the army arranged in military formation by the sons of Pandu, King Duryodhana went to his teacher and spoke the following words.
    
    O my teacher, behold the great army of the sons of Pandu, so expertly arranged by your intelligent disciple the son of Drupada.
    """
    
    y = height - 80
    for line in text.strip().split('\n'):
        c.drawString(50, y, line.strip())
        y -= 20
        
    c.showPage()
    c.save()
    print(f"Created demo PDF: {filename}")

def create_hindi_demo_pdf(filename="gita_demo_hindi.pdf"):
    """Creates a PDF with REAL Hindi Bhagwat Gita content using a downloaded font."""
    
    # 1. Download a Hindi-supporting font (Noto Sans Devanagari)
    font_path = "NotoSansDevanagari-Regular.ttf"
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"
    
    try:
        download_font(font_path, font_url)
        
        # 2. Register the font
        pdfmetrics.registerFont(TTFont('HindiFont', font_path))
        
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # Title Page
        c.setFont("HindiFont", 24)
        c.drawCentredString(width / 2, height / 2, "भगवद गीता डेमो (Bhagwat Gita Demo)")
        c.showPage()

        # Chapter 1
        c.setFont("HindiFont", 18)
        c.drawString(50, height - 50, "अध्याय 1 (Chapter 1)")
        c.setFont("HindiFont", 12)
        
        # Real Hindi Text
        hindi_text = """
        धृतराष्ट्र बोले: हे संजय! धर्मभूमि कुरुक्षेत्र में एकत्रित, युद्ध की इच्छा वाले मेरे और पाण्डु के पुत्रों ने क्या किया?

        संजय बोले: उस समय राजा दुर्योधन ने व्यूहरचनायुक्त पाण्डवों की सेना को देखकर और द्रोणाचार्य के पास जाकर यह वचन कहा।

        हे आचार्य! आपके बुद्धिमान् शिष्य द्रुपदपुत्रधृष्टद्युम्नद्वारा व्यूहाकार खड़ी की हुई पाण्डुपुत्रों की इस बड़ी भारी सेना को देखिये।
        """
        
        y = height - 80
        for line in hindi_text.strip().split('\n'):
            line = line.strip()
            if line:
                c.drawString(50, y, line)
                y -= 20
        
        c.save()
        print(f"Created REAL Hindi demo PDF: {filename}")
        
        # Cleanup font file to keep directory clean
        if os.path.exists(font_path):
            os.remove(font_path)
            
    except Exception as e:
        print(f"Failed to create Hindi PDF: {e}")
        print("Falling back to dummy PDF...")
        # Fallback if font download fails (e.g. no internet)
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 500, "Hindi Font Download Failed. This is a placeholder.")
        c.save()

def create_demo_avatar(filename="assets/krishna.jpg"):
    """Creates a simple placeholder avatar image."""
    if not os.path.exists("assets"):
        os.makedirs("assets")
    
    if os.path.exists(filename):
        print(f"Avatar image already exists at {filename}. Skipping generation.")
        return

    img = Image.new('RGB', (512, 512), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    d.ellipse((100, 100, 412, 412), fill=(255, 200, 150), outline=(0, 0, 0))
    d.ellipse((180, 200, 220, 220), fill=(255, 255, 255), outline=(0, 0, 0))
    d.ellipse((292, 200, 332, 220), fill=(255, 255, 255), outline=(0, 0, 0))
    d.ellipse((195, 205, 205, 215), fill=(0, 0, 0))
    d.ellipse((307, 205, 317, 215), fill=(0, 0, 0))
    d.arc((200, 300, 312, 350), start=0, end=180, fill=(0, 0, 0))
    img.save(filename)
    print(f"Created demo avatar: {filename}")

if __name__ == "__main__":
    create_demo_pdf()
    create_hindi_demo_pdf()
    create_demo_avatar()
