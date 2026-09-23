import math
import re
import os
import base64
import streamlit as st
from PIL import Image, ImageOps
import pytesseract
from weasyprint import HTML

st.set_page_config(page_title="Suja's Kitchen Card Generator", layout="centered")
st.title("SUJA'S KITCHEN - Name Card Generator")

CARDS_PER_PAGE = 10
LOGO_PATH = "logo.png"  # Make sure this matches your uploaded logo filename on GitHub

if "dish_text" not in st.session_state:
    st.session_state.dish_text = ""

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return ""

def clean_and_extract_food_names(raw_ocr_text):
    lines = raw_ocr_text.split('\n')
    extracted_dishes = []
    
    header_keywords = ["VAN OORD", "PATHRAM", "23RD", "SEP", "PAX", "ITEM", "QTY", "SHEET"]
    
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

def generate_html_pdf(items_list):
    total_pages = math.ceil(len(items_list) / CARDS_PER_PAGE)
    pages_html = ""
    logo_base64 = get_image_base64(LOGO_PATH)
    
    logo_html = f'<img src="{logo_base64}" class="card-logo" />' if logo_base64 else ''

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
          /* INCREASED CELL SPACING BY 5% (FROM 6mm TO 8mm) */
          gap: 8mm;
          page-break-after: always;
        }}
        .card-box {{
          position: relative;
          /* INCREASED BORDER THICKNESS (FROM 2px TO 3.5px) */
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
          
          /* INNER PADDING */
          padding: 16px 20px;
        }}
        .card-logo {{
          position: absolute;
          top: 8px;
          right: 10px;
          width: 32px;
          height: 32px;
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
uploaded_image = st.file_uploader("1. Upload Photo from WhatsApp or Camera", type=["jpg", "jpeg", "png"])

if uploaded_image:
    img = Image.open(uploaded_image)
    img = ImageOps.exif_transpose(img)
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Extract Dish Names", type="primary"):
        raw_ocr = pytesseract.image_to_string(img)
        cleaned_list = clean_and_extract_food_names(raw_ocr)
        st.session_state.dish_text = "\n".join(cleaned_list)

st.subheader("2. Review & Edit Items (1 per line)")
items_input = st.text_area("Dish List", value=st.session_state.dish_text, height=250)
st.session_state.dish_text = items_input

items_list = [line.strip() for line in items_input.split("\n") if line.strip()]

if items_list:
    if st.button("Generate Final PDF"):
        pdf_bytes = generate_html_pdf(items_list)
        st.success(f"Generated {len(items_list)} cards across {math.ceil(len(items_list)/10)} page(s)!")
        
        st.download_button(
            label="📥 Download Printable PDF",
            data=pdf_bytes,
            file_name="Printable_Mess_Cards.pdf",
            mime="application/pdf"
        )
