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

def clean_and_extract_food_names(raw_ocr_text):
    """
    Parses table OCR text line by line:
    - Ignores header/date rows.
    - Excludes items with no entry, empty string, or '-' in the Qty column.
    - Strips parentheses and splits slashes '/'.
    """
    lines = raw_ocr_text.split('\n')
    extracted_dishes = []
    
    # Headers and date keywords to ignore completely
    header_keywords = ["VAN OORD", "PATHRAM", "23RD", "SEP", "PAX", "ITEM", "QTY"]
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # Skip top header rows
        if any(keyword in clean_line.upper() for keyword in header_keywords):
            continue

        # Detect quantity pattern at the end of the line (e.g., "6 Ltr", "8 Kg", "200 Ps", "20/40", "-")
        # Match dish name vs quantity
        qty_match = re.search(r'^(.*?)\s+([\d\/\.\s]*(?:Ltr|Kg|Ps|Pcs)?|-)\s*$', clean_line, re.IGNORECASE)
        
        if qty_match:
            item_name = qty_match.group(1).strip()
            qty_val = qty_match.group(2).strip()
            
            # Rule: Ignore items where quantity is '-' or empty
            if not qty_val or qty_val == "-":
                continue
        else:
            # Fallback if regex didn't split quantity
            item_name = clean_line

        # Remove parenthesis content e.g. "(Boneless)" -> ""
        item_name = re.sub(r'\(.*?\)', '', item_name).strip()
        
        # Remove any residual trailing digits/units that weren't caught
        item_name = re.sub(r'\s+\d+\s*(Ltr|Kg|Ps|Pcs)?$', '', item_name, flags=re.IGNORECASE).strip()

        if not item_name or item_name.isdigit() or item_name == "-":
            continue

        # Split items with slashes (e.g. "Aloo/subji" -> "Aloo", "Subji")
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

def draw_centered_text(c, text, center_x, center_y, max_width, max_font_size=16, min_font_size=8):
    """Centers food name inside card frame without overflowing borders."""
    font_name = "Helvetica-Bold"
    font_size = max_font_size
    c.setFont(font_name, font_size)
    
    # Scale down font size dynamically if text is wide
    while c.stringWidth(text, font_name, font_size) > max_width and font_size > min_font_size:
        font_size -= 0.5
        c.setFont(font_name, font_size)
        
    y_adjusted = center_y - (font_size * 0.35)
    c.drawCentredString(center_x, y_adjusted, text)

def generate_overlay(page_items):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    c.setFillColorRGB(0.1, 0.1, 0.1)

    for idx, item in enumerate(page_items):
        col = idx % COLUMNS
        row = idx // COLUMNS
        
        x_left = col * CARD_WIDTH
        y_bottom = PAGE_HEIGHT - ((row + 1) * CARD_HEIGHT)
        
        # Exact geometric center of the card box
        center_x = x_left + (CARD_WIDTH / 2.0)
        center_y = y_bottom + (CARD_HEIGHT * 0.36)
        
        # Keep generous side margins to avoid touching card borders
        max_width = CARD_WIDTH - (28 * mm)
        
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
