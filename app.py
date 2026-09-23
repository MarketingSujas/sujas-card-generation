import io
import math
import re
import os
import streamlit as st
from PIL import Image
import pytesseract
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

st.set_page_config(page_title="Suja's Kitchen Card Generator", layout="centered")
st.title("SUJA'S KITCHEN - Name Card Generator")

PAGE_WIDTH, PAGE_HEIGHT = A4
COLUMNS, ROWS = 2, 5
CARDS_PER_PAGE = COLUMNS * ROWS
CARD_WIDTH = PAGE_WIDTH / COLUMNS
CARD_HEIGHT = PAGE_HEIGHT / ROWS

TEMPLATE_PATH = "Mess Name cards template.pdf"

if "dish_text" not in st.session_state:
    st.session_state.dish_text = ""

def clean_and_split_items(raw_text):
    lines = raw_text.split('\n')
    cleaned_items = []
    
    # Common non-dish keywords, quantities, and dates to remove
    ignore_patterns = [
        r'PATHRAM', r'SHEET', r'PAX', r'23RD', r'SEP', r'ITEM', r'QTY',
        r'LTR', r'KG', r'PS', r'^\d+$', r'^-+$'
    ]
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Skip header lines, date lines, or quantity-only lines
        if any(re.search(pat, line_clean.upper()) for pat in ignore_patterns):
            continue

        # Strip out parentheses and their contents, e.g. "(Boneless)" -> ""
        text = re.sub(r'\(.*?\)', '', line_clean).strip()
        
        # Strip out quantities appended at the end of line (e.g. "6 Ltr", "8 Kg", "85 Ps")
        text = re.sub(r'\s+\d+\s*(Ltr|Kg|Ps|Liters|Kgs|Pcs)?$', '', text, flags=re.IGNORECASE).strip()
        
        # Remove standalone digits or special characters
        if not text or text.isdigit() or text == "-":
            continue

        # Split items separated by / (e.g. "Aloo/subji" -> "Aloo", "Subji")
        if '/' in text:
            parts = [p.strip() for p in text.split('/') if p.strip()]
            for p in parts:
                if p.title() not in cleaned_items:
                    cleaned_items.append(p.title())
        else:
            if text.title() not in cleaned_items:
                cleaned_items.append(text.title())
            
    return cleaned_items

def draw_centered_text(c, text, center_x, center_y, max_width, max_font_size=15, min_font_size=8):
    """Resizes and vertically/horizontally centers text cleanly inside card box."""
    font_name = "Helvetica-Bold"
    font_size = max_font_size
    c.setFont(font_name, font_size)
    
    # Scale down font size if string width exceeds card margin width
    while c.stringWidth(text, font_name, font_size) > max_width and font_size > min_font_size:
        font_size -= 0.5
        c.setFont(font_name, font_size)
        
    # Vertical offset calculation for exact font center alignment
    y_adjusted = center_y - (font_size * 0.35)
    c.drawCentredString(center_x, y_adjusted, text)

def generate_overlay(page_items):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    c.setFillColorRGB(0.1, 0.1, 0.1) # Charcoal black text

    for idx, item in enumerate(page_items):
        col = idx % COLUMNS
        row = idx // COLUMNS
        
        x_left = col * CARD_WIDTH
        y_bottom = PAGE_HEIGHT - ((row + 1) * CARD_HEIGHT)
        
        # True Card Center Point
        center_x = x_left + (CARD_WIDTH / 2.0)
        # Position centered vertically below the top logo header
        center_y = y_bottom + (CARD_HEIGHT * 0.35)
        
        # Horizontal safety width padding (keeps text away from side borders)
        max_width = CARD_WIDTH - (30 * mm)
        
        if item:
            draw_centered_text(c, str(item).strip(), center_x, center_y, max_width)

    c.save()
    packet.seek(0)
    return packet

def create_printable_pdf(template_path, items_list):
    writer = PdfWriter()
    total_pages = math.ceil(len(items_list) / CARDS_PER_PAGE)

    for p in range(total_pages):
        page_items = items_list[p * CARDS_PER_PAGE : (p + 1) * CARDS_PER_PAGE]
        overlay_stream = generate_overlay(page_items)
        overlay_reader = PdfReader(overlay_stream)
        
        template_reader = PdfReader(template_path)
        page_copy = template_reader.pages[0]
        page_copy.merge_page(overlay_reader.pages[0])
        writer.add_page(page_copy)
        
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream

# --- App UI ---
uploaded_image = st.file_uploader("1. Upload Photo from WhatsApp or Camera", type=["jpg", "jpeg", "png"])

if uploaded_image:
    img = Image.open(uploaded_image)
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Extract Dish Names"):
        raw_ocr = pytesseract.image_to_string(img)
        cleaned_list = clean_and_split_items(raw_ocr)
        st.session_state.dish_text = "\n".join(cleaned_list)

st.subheader("2. Review & Edit Items (1 per line)")
items_input = st.text_area("Dish List", value=st.session_state.dish_text, height=250)

# Synchronize edited state
st.session_state.dish_text = items_input

items_list = [line.strip() for line in items_input.split("\n") if line.strip()]

if items_list:
    if st.button("Generate Final PDF"):
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"Template file '{TEMPLATE_PATH}' not found in GitHub repository. Please upload it.")
        else:
            pdf_out = create_printable_pdf(TEMPLATE_PATH, items_list)
            st.success(f"Generated {len(items_list)} cards across {math.ceil(len(items_list)/10)} page(s)!")
            
            st.download_button(
                label="📥 Download Printable PDF",
                data=pdf_out,
                file_name="Printable_Mess_Cards.pdf",
                mime="application/pdf"
            )
