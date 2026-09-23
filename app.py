import math
import re
import os
import base64
import numpy as np
import cv2
import streamlit as st
from PIL import Image, ImageOps
import pytesseract
from weasyprint import HTML

st.set_page_config(page_title="Suja's Kitchen Card Generator", layout="centered")
st.title("SUJA'S KITCHEN - Name Card Generator")

CARDS_PER_PAGE = 10

if "dish_text" not in st.session_state:
    st.session_state.dish_text = ""

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

def remove_table_lines_and_clean(pil_img):
    """
    1. Removes table grid lines/borders so Tesseract doesn't fail on complex menus.
    2. Converts to high-contrast black and white.
    """
    img = ImageOps.exif_transpose(pil_img)
    img_np = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    # Threshold image to binary
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Detect and remove horizontal grid lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    remove_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Detect and remove vertical grid lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    remove_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    
    # Combine table lines mask and subtract from image
    table_lines = cv2.add(remove_horizontal, remove_vertical)
    cleaned_binary = cv2.subtract(thresh, table_lines)
    
    # Invert back to black text on white background
    final_img = cv2.bitwise_not(cleaned_binary)
    return Image.fromarray(final_img)

def extract_first_column_dishes(pil_img):
    cleaned_img = remove_table_lines_and_clean(pil_img)
    
    # Run OCR on cleaned image
    data = pytesseract.image_to_data(cleaned_img, output_type=pytesseract.Output.DICT)
    
    width, _ = cleaned_img.size
    first_col_limit = width * 0.50  # Capture items in the left-hand column
    
    lines_dict = {}
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        left = data['left'][i]
        line_num = data['line_num'][i]
        
        if text and left < first_col_limit:
            lines_dict.setdefault(line_num, []).append(text)

    extracted_dishes = []
    ignore_keywords = [
        "ITEM", "QTY", "PAX", "SHEET", "OFFICE", "JAFZA", "DATE", "VAN OORD", "PATHRAM",
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
    ]

    for line_words in lines_dict.values():
        clean_line = " ".join(line_words).strip()
        if not clean_line:
            continue

        if any(keyword in clean_line.upper() for keyword in ignore_keywords):
            continue

        if re.search(r'\b\d{1,2}(st|nd|rd|th)?[\/\-\s]', clean_line, re.IGNORECASE):
            continue

        # 1. Remove text inside () completely
        clean_line = re.sub(r'\(.*?\)', '', clean_line).strip()
        clean_line = re.sub(r'\s+\d+\s*(Ltr|Kg|Ps|Pcs)?$', '', clean_line, flags=re.IGNORECASE).strip()

        if not clean_line or clean_line.isdigit() or clean_line == "-" or len(clean_line) < 2:
            continue

        # 2. Split items containing slashes '/'
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
          z-index: 1;
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
          
          /* TOP-MOST LAYER STYLING */
          position: relative;
          z-index: 10;
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
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Extract Dish Names", type="primary"):
        with st.spinner("Extracting dish names..."):
            try:
                cleaned_list = extract_first_column_dishes(img)
                st.session_state.dish_text = "\n".join(cleaned_list)
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

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
