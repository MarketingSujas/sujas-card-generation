import math
import os
import base64
import streamlit as st
from weasyprint import HTML

st.set_page_config(page_title="Suja's Kitchen Generator", layout="centered")
st.title("SUJA'S KITCHEN - Name Card & Menu Generator")

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
          
          padding-top: 50px;
          padding-bottom: 12px;
          padding-left: 14px;
          padding-right: 14px;
        }}
        .card-logo {{
          position: absolute;
          top: 6px;
          right: 6px;
          width: 60px;
          height: 60px;
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
          font-size: 18px;
          
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

def generate_menu_pdf(soups_salads, mains_desserts, logo_b64):
    """Placeholder renderer for Menu Layout (ready for second design rules)."""
    logo_html = f'<img src="{logo_b64}" class="menu-logo" />' if logo_b64 else ''
    
    soups_html = "".join([f"<li>{item}</li>" for item in soups_salads])
    mains_html = "".join([f"<li>{item}</li>" for item in mains_desserts])

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
          padding: 15mm;
          font-family: "Helvetica", "Arial", sans-serif;
          color: #000000;
        }}
        .menu-header {{
          text-align: center;
          position: relative;
          margin-bottom: 30px;
        }}
        .menu-logo {{
          width: 90px;
          height: 90px;
          object-fit: contain;
        }}
        .section-title {{
          color: #ca113b;
          font-size: 22px;
          border-bottom: 2px solid #ca113b;
          padding-bottom: 5px;
          margin-top: 25px;
        }}
        ul {{
          list-style-type: none;
          padding: 0;
        }}
        li {{
          font-size: 16px;
          font-weight: bold;
          margin-bottom: 10px;
        }}
      </style>
    </head>
    <body>
      <div class="menu-header">
        {logo_html}
        <h1 style="color: #ca113b; margin-top: 10px;">TODAY'S MENU</h1>
      </div>

      <div class="section-title">Soups & Salads</div>
      <ul>{soups_html}</ul>

      <div class="section-title">Mains & Desserts</div>
      <ul>{mains_html}</ul>
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

# Binary Mode Selector
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
    
    soups_salads_text = st.text_area("Soups & Salads (1 per line)", height=150)
    mains_desserts_text = st.text_area("Mains & Desserts (1 per line)", height=200)

    soups_salads = [line.strip() for line in soups_salads_text.split("\n") if line.strip()]
    mains_desserts = [line.strip() for line in mains_desserts_text.split("\n") if line.strip()]

    if soups_salads or mains_desserts:
        if st.button("Generate Menu PDF", type="primary"):
            pdf_bytes = generate_menu_pdf(soups_salads, mains_desserts, logo_b64)
            st.success("Generated Menu PDF!")
            
            st.download_button(
                label="📥 Download Menu PDF",
                data=pdf_bytes,
                file_name="Printable_Menu.pdf",
                mime="application/pdf"
            )
