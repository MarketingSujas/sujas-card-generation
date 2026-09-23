import math
import re
import os
import base64
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
from weasyprint import HTML
import easyocr

st.set_page_config(page_title="Suja's Kitchen Card Generator", layout="centered")
st.title("SUJA'S KITCHEN - Name Card Generator")

CARDS_PER_PAGE = 10

if "dish_text" not in st.session_state:
    st.session_state.dish_text = ""

@st.cache_resource
def load_ocr_reader():
    """Loads the free EasyOCR deep learning model into memory once."""
    return easyocr.Reader(['en'], gpu=False)

def load_logo_base64():
    possible_filenames = [
        "logo.png", "logo.jpeg", "logo.jpg",
        "Suja's Transparent Logo.jpeg", "Suja's Transparent Logo.png",
        "Suja's Transparent Logo.jpg"
    ]
    for filename in possible_filenames:
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                mime = "image/png" if filename.endswith(".png") else "image/jpeg"
                return f"data:{mime};base64,{encoded}"
    return ""

def filter_and_clean_dishes(ocr_results):
    """
    Custom extraction pipeline:
    1. Keeps only items located in the left-most column (x-position filter).
    2. Strips out all parenthetical content like (ltr) or (Boneless).
    3. Discards dates, pure numbers, and headers.
    4. Splits items separated by slashes '/' into individual entries.
    """
    if not ocr_results:
        return []

    # 1. Determine bounding box for the first column (x-axis coordinates)
    x_midpoints = [bbox[0][0] for bbox, text, prob in ocr_results]
    min_x = min(x_midpoints)
    max_x = max(x_midpoints)
    x_range = max_x - min_x
    
    # Threshold to isolate the first column (~45% of total horizontal text width)
    first_col_threshold = min_x + (x_range * 0.45) if x_range > 0 else min_x + 200

    extracted_dishes = []
    
    ignore_keywords = [
        "ITEM", "QTY", "PAX", "SHEET", "OFFICE", "JAFZA", "DATE", "VAN OORD", "PATHRAM",
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
    ]

    for bbox, text, prob in ocr_results:
        x_start = bbox[0][0]
        
        # Only process text in the first column
        if x_start > first_col_threshold:
            continue
            
        clean_line = text.strip()
        if not clean_line:
            continue

        # Ignore explicit table headers or dates
        if any(keyword in clean_line.upper() for keyword in ignore_keywords):
            continue

        if re.search(r'\b\d{1,2}(st|nd|rd|th)?[\/\-\s]', clean_line, re.IGNORECASE):
            continue

        # Remove parentheses and everything inside them e.g. "Chicken Khorma (ltr)" -> "Chicken Khorma"
        clean_line = re.sub(r'\(.*?\)', '', clean_line).strip()
        
        # Remove trailing single quantities or standalone units
        clean_line = re.sub(r'\s+\d+\s*(Ltr|Kg|Ps|Pcs)?$', '', clean_line, flags=re.IGNORECASE).strip()

        # Reject pure numbers, dashes, or short noise strings
        if not clean_line or clean_line.isdigit() or clean_line == "-" or len(clean_line) < 2:
            continue

        # Split items separated by slashes '/' into distinct entries
        if '/' in clean_line:
            parts = [p.strip().title() for p in clean_line.split('/') if p.strip()]
            for p in parts:
                if p not in extracted_dishes and len(p) > 1:
                    extracted_dishes.append(p)
        else:
            formatted_name = clean_line.title()
            if formatted_name not in extracted_dishes:
                extracted_dishes.append(formatted_name)

    return extracted_dishes

def generate_html_pdf(items_list, logo_b64):
    total_pages = math.ceil(len(items_list) / CARDS_PER_PAGE)
    pages_html = ""
    
    logo_html = f'<img src="{logo_b64}" class="card-logo" />' if logo_b64 else ''

    for p in range(total_pages):
        page_items = items_list[p * CARDS_PER_PAGE : (p + 1) * CARDS_PER_PAGE]
        
        cards_html = ""
        for item in page_items:
            cards_html += f"""
            <div class="card-box">
              {logo_html}
              <p class="dish-name">{item}</p>
            </div>
            """
            
        empty_slots = CARDS_PER_PAGE - len(page_items)
        for _ in range(empty_slots):
            cards_html += f'<div class="card-box">{logo_html}</div>'

        pages_html += f'<div class="grid-container">{cards_html}</div>'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8" />
      <style>
        @page {{
          size: A4;
          margin: 0;
        }}
        body {{
          margin: 0;
          padding: 0;
          font-family: "Helvetica", "Arial", sans-serif;
          background-color: #ffffff;
        }}
        .grid-container {{
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          grid-template-rows: repeat(5, 1fr);
          width: 210mm;
          height: 297mm;
          box-sizing: border-box;
          padding: 8mm;
          gap: 8mm;
          page-break-after: always;
        }}
        .card-box {{
          position: relative;
          border: 3.5px solid #ca113b;
          border-radius: 14px;
          box-sizing: border-box;
          background: #ffffff;
          overflow: hidden;
          
          /* FLEXBOX CENTERING */
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          text-align: center;
          
          padding: 16px 20px;
        }}
        .card-logo {{
          position: absolute;
          top: 8px;
          right: 8px;
          width: 75px;
          height: 75px;
          object-fit: contain;
        }}
        .dish-name {{
          color: #000000;
          font-weight: 700;
          line-height: 1.25;
          width: 100%;
          margin: 0;
          
          word-wrap: break-word;
          overflow-wrap: break-word;
          
          font-size: 20px;
        }}
      </style>
    </head>
    <body>
      {pages_html}
    </body>
    </html>
    """
    
    return HTML(string=html_content).write_pdf()

# --- User Interface ---
logo_b64 = load_logo_base64()

if not logo_b64:
    logo_file = st.file_uploader("Upload Brand Logo (PNG/JPEG)", type=["png", "jpg", "jpeg"])
    if logo_file:
        encoded_logo = base64.b64encode(logo_file.read()).decode("utf-8")
        logo_b64 = f"data:{logo_file.type};base64,{encoded_logo}"

uploaded_image = st.file_uploader("1. Upload Photo from WhatsApp or Camera", type=["jpg", "jpeg", "png"])

if uploaded_image:
    img = Image.open(uploaded_image)
    img = ImageOps.exif_transpose(img)
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Extract Dish Names", type="primary"):
        with st.spinner("Extracting dish names from first column..."):
            reader = load_ocr_reader()
            img_np = np.array(img.convert('RGB'))
            # Detail=1 yields bounding box metadata needed to isolate the first column
            results = reader.readtext(img_np, detail=1)
            cleaned_list = filter_and_clean_dishes(results)
            st.session_state.dish_text = "\n".join(cleaned_list)

st.subheader("2. Review & Edit Items (1 per line)")
items_input = st.text_area("Dish List", value=st.session_state.dish_text, height=250)
st.session_state.dish_text = items_input

items_list = [line.strip() for line in items_input.split("\n") if line.strip()]

if items_list:
    if st.button("Generate Final PDF"):
        pdf_bytes = generate_html_pdf(items_list, logo_b64)
        st.success(f"Generated {len(items_list)} cards across {math.ceil(len(items_list)/10)} page(s)!")
        
        st.download_button(
            label="📥 Download Printable PDF",
            data=pdf_bytes,
            file_name="Printable_Mess_Cards.pdf",
            mime="application/pdf"
        )
