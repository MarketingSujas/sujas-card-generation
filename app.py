import math
import os
import base64
import streamlit as st
from weasyprint import HTML

st.set_page_config(page_title="Suja's Kitchen Generator", layout="centered")
st.title("SUJA'S KITCHEN - Card & Menu Generator")

CARDS_PER_PAGE = 10

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

def generate_cards_pdf(items_list, logo_b64):
    total_pages = math.ceil(len(items_list) / CARDS_PER_PAGE)
    pages_html = ""
    logo_html = f'<img src="{logo_b64}" class="card-logo" />' if logo_b64 else ''

    for p in range(total_pages):
        page_items = items_list[p * CARDS_PER_PAGE : (p + 1) * CARDS_PER_PAGE]
        cards_html = ""
        for item in page_items:
            # Multi-tier text size scaling based on length
            text_len = len(item)
            if text_len <= 16:
                size_class = "size-25"
            elif text_len <= 26:
                size_class = "size-20"
            elif text_len <= 40:
                size_class = "size-16"
            else:
                size_class = "size-13"

            cards_html += f"""
            <div class="card-box">
              {logo_html}
              <div class="text-wrapper">
                <p class="dish-name {size_class}">{item}</p>
              </div>
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
          font-family: "Helvetica Neue", "Helvetica", "Arial", sans-serif;
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
        /* FIXED DIMENSIONS - NEVER DEFORMS */
        .card-box {{
          position: relative;
          width: 100%;
          height: 100%;
          border: 3.5px solid #ca113b;
          border-radius: 14px;
          box-sizing: border-box;
          background: #ffffff;
          overflow: hidden;
        }}
        .card-logo {{
          position: absolute;
          top: 6px;
          right: 6px;
          width: 50px;
          height: 50px;
          object-fit: contain;
          z-index: 2;
        }}
        /* ABSOLUTELY POSITIONED CENTERED CONTAINER */
        .text-wrapper {{
          position: absolute;
          top: 52px;
          bottom: 8px;
          left: 10px;
          right: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          overflow: hidden;
          z-index: 10;
        }}
        .dish-name {{
          color: #000000;
          font-weight: 700;
          line-height: 1.2;
          width: 100%;
          margin: 0;
          word-wrap: break-word;
          overflow-wrap: break-word;
          text-align: center;
        }}
        /* TEXT SHRINK TIERS */
        .size-25 {{ font-size: 25px; }}
        .size-20 {{ font-size: 20px; }}
        .size-16 {{ font-size: 16px; }}
        .size-13 {{ font-size: 13px; }}
      </style>
    </head>
    <body>
      {pages_html}
    </body>
    </html>
    """
    return HTML(string=html_content).write_pdf()

def generate_menu_pdf(client_name, soups_salads, mains_desserts, logo_b64):
    logo_html = f'<img src="{logo_b64}" class="brand-logo" />' if logo_b64 else ''
    client_title = client_name.strip().upper() if client_name else "DABUR"
    
    soups_items_html = "".join([f'<div class="menu-item">{item.strip().upper()}</div>' for item in soups_salads])
    mains_items_html = "".join([f'<div class="menu-item">{item.strip().upper()}</div>' for item in mains_desserts])

    pages_html = ""

    # Page 1: Soups & Salads
    if soups_salads:
        pages_html += f"""
        <div class="menu-page">
          <div class="menu-border">
            <div class="header">
              {logo_html}
              <div class="category-title">Soups & Salads</div>
              <div class="divider-line"></div>
              <div class="client-name">{client_title}</div>
            </div>
            <div class="items-container">
              {soups_items_html}
            </div>
          </div>
        </div>
        """

    # Page 2: Mains & Dessert
    if mains_desserts:
        pages_html += f"""
        <div class="menu-page">
          <div class="menu-border">
            <div class="header">
              {logo_html}
              <div class="category-title">Mains & Dessert</div>
              <div class="divider-line"></div>
              <div class="client-name">{client_title}</div>
            </div>
            <div class="items-container">
              {mains_items_html}
            </div>
          </div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8" />
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap" rel="stylesheet">
      <style>
        @page {{
          size: A4;
          margin: 0;
        }}
        body {{
          margin: 0;
          padding: 0;
          font-family: "Helvetica Neue", "Helvetica", "Arial", sans-serif;
          background-color: #ffffff;
        }}
        .menu-page {{
          width: 210mm;
          height: 297mm;
          box-sizing: border-box;
          padding: 6mm;
          page-break-after: always;
        }}
        /* ULTRA-THICK RED BORDER */
        .menu-border {{
          width: 100%;
          height: 100%;
          border: 24px solid #c8102e;
          box-sizing: border-box;
          padding: 12mm 10mm;
          display: flex;
          flex-direction: column;
          align-items: center;
        }}
        .header {{
          display: flex;
          flex-direction: column;
          align-items: center;
          margin-bottom: 10px;
        }}
        .brand-logo {{
          width: 135px;
          height: 135px;
          object-fit: contain;
          margin-bottom: 10px;
        }}
        /* CURSIVE HEADING IN BLACK */
        .category-title {{
          color: #000000;
          font-family: 'Dancing Script', 'Great Vibes', 'Brush Script MT', cursive;
          font-size: 64px;
          font-weight: 700;
          margin-bottom: 4px;
          line-height: 1.05;
        }}
        /* UNDERLINE BELOW HEADING */
        .divider-line {{
          width: 180px;
          height: 2.5px;
          background-color: #c8102e;
          margin-top: 2px;
          margin-bottom: 8px;
        }}
        /* SMALL CLIENT/EVENT NAME BELOW DIVIDER */
        .client-name {{
          color: #000000;
          font-size: 18px;
          font-weight: 700;
          letter-spacing: 2px;
          opacity: 0.85;
        }}
        /* EQUIDISTANT VERTICAL DISTRIBUTION */
        .items-container {{
          width: 100%;
          flex-grow: 1;
          display: flex;
          flex-direction: column;
          justify-content: space-evenly;
          align-items: center;
          padding-top: 15px;
          padding-bottom: 15px;
        }}
        /* ALL-CAPS MENU DISH ITEMS */
        .menu-item {{
          color: #000000;
          font-size: 32px;
          font-weight: 800;
          letter-spacing: 1px;
          line-height: 1.3;
          text-align: center;
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

doc_type = st.radio("Select Document Type", ["Cards", "Menus"], horizontal=True)

if doc_type == "Cards":
    st.subheader("Card Items (1 per line)")
    card_text = st.text_area("Enter Dish Names", height=250)
    card_items = [line.strip() for line in card_text.split("\n") if line.strip()]

    if card_items:
        if st.button("Generate Cards PDF", type="primary"):
            pdf_bytes = generate_cards_pdf(card_items, logo_b64)
            st.success(f"Generated {len(card_items)} card(s) across {math.ceil(len(card_items)/10)} page(s)!")
            
            st.download_button(
                label="📥 Download Printable Cards PDF",
                data=pdf_bytes,
                file_name="Printable_Name_Cards.pdf",
                mime="application/pdf"
            )

else:
    st.subheader("Menu Items")
    
    client_name = st.text_input("Client / Event Name", value="DABUR")
    soups_salads_text = st.text_area("Soups & Salads (1 per line)", height=150)
    mains_desserts_text = st.text_area("Mains & Dessert (1 per line)", height=200)

    soups_salads = [line.strip() for line in soups_salads_text.split("\n") if line.strip()]
    mains_desserts = [line.strip() for line in mains_desserts_text.split("\n") if line.strip()]

    if soups_salads or mains_desserts:
        if st.button("Generate Menu PDF", type="primary"):
            pdf_bytes = generate_menu_pdf(client_name, soups_salads, mains_desserts, logo_b64)
            st.success("Generated Menu PDF!")
            
            st.download_button(
                label="📥 Download Menu PDF",
                data=pdf_bytes,
                file_name="Printable_Menu.pdf",
                mime="application/pdf"
            )
