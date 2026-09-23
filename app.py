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
from reportlab.lib.colors import HexColor
from reportlab.utils import simpleSplit

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

def clean_and_extract_food_names(raw_ocr_text):
    lines = raw_ocr_text.split('\n')
    extracted_dishes = []
    
    header_keywords = ["VAN OORD", "PATHRAM", "23RD", "SEP", "PAX", "ITEM", "QTY"]
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        if any(keyword in clean_line.upper() for keyword in header_keywords):
            continue

        qty_match = re.search(r'^(.*?)\s+([\d\/\.\s]*(?:Ltr|Kg|Ps|Pcs)?|-)\s*$', clean_line, re.IGNORECASE)
        
        if qty_match:
            item_name = qty_match.group(1).strip()
            qty_val = qty_match.group(2).strip()
            
            if not qty_val or qty_val == "-":
                continue
        else:
            item_name = clean_line

        item_name = re.sub(r'\(.*?\)', '', item_name).strip()
        item_name = re.sub(r'\s+\d+\s*(Ltr|Kg|Ps|Pcs)?$', '', item_name, flags=re.IGNORECASE).strip()

        if not item_name or item_name.isdigit() or item_name == "-":
            continue

        if '/' in item_name:
            parts = [p.strip().title() for p in item_name.split('/') if p.strip()]
            for p in parts:
                if p not in extracted_dishes:
                    extracted_dishes.append(p)
        else:
            formatted_name = item_name.title()
            if formatted_name not in extracted_dishes:
                extracted_dishes.append(formatted_name)
                
    return extracted_dishes

def draw_centered_text(c, text, center_x, center_y, max_width, start_font_size=15, min_font_size=9):
    """Draws pure black text, perfectly centered horizontally and vertically with multi-line wrap if long."""
    font_name = "Helvetica-Bold"
    c.setFont(font_name, start_font_size)
    c.setFillColor(HexColor("#000000"))  # Pure Black

    # Split text into multiple lines if longer than max_width
    lines = simpleSplit(text, font_name, start_font_size, max_width)
    
    # If still too long, reduce font size
    font_size = start_font_size
    while len(lines) > 2 and font_size > min_font_size:
        font_size -= 0.5
        lines = simpleSplit(text, font_name, font_size, max_width)
        
    c.setFont(font_name, font_size)
    line_height = font_size * 1.2
    total_height = len(lines) * line_height
    
    # Starting Y position for vertical center
    start_y = center_y + (total_height / 2.0) - (font_size * 0.7)
    
    for i, line in enumerate(lines):
        y_pos = start_y - (i * line_height)
        c.drawCentredString(center_x, y_pos, line)

def generate_overlay(page_items):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    for idx, item in enumerate(page_items):
        col = idx % COLUMNS
        row = idx // COLUMNS
        
        x_left = col * CARD_WIDTH
        y_bottom = PAGE_HEIGHT - ((row + 1) * CARD_HEIGHT)
        
        # Exact horizontal & vertical center of each card frame
        center_x = x_left + (CARD_WIDTH / 2.0)
        center_y = y_bottom + (CARD_HEIGHT * 0.38)
        
        # Strict inner printable boundary (prevents overflow off card borders)
        max_width = CARD_WIDTH - (40 * mm)
        
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
        cleaned_list = clean_and_extract_food_names(raw_ocr)
        st.session_state.dish_text = "\n".join(cleaned_list)

st.subheader("2. Review & Edit Items (1 per line)")
items_input = st.text_area("Dish List", value=st.session_state.dish_text, height=250)

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
