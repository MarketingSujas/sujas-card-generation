import math
import os
import base64
import streamlit as st
from PIL import Image, ImageOps
from weasyprint import HTML
from google import genai

st.set_page_config(page_title="Suja's Kitchen Card Generator", layout="centered")
st.title("SUJA'S KITCHEN - Name Card Generator")

CARDS_PER_PAGE = 10

if "dish_text" not in st.session_state:
    st.session_state.dish_text = ""

# Securely retrieve Gemini API key from Streamlit Cloud Secrets
gemini_api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

def load_logo_base64():
    """Locates the logo in the repo and converts it to a base64 data URL."""
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

def extract_dishes_with_gemini(pil_img, api_key):
    """Uses Gemini Flash to extract dish names accurately from photos."""
    client = genai.Client(api_key=api_key)
    
    # Fix orientation from mobile camera EXIF metadata
    oriented_img = ImageOps.exif_transpose(pil_img)
    
    prompt = """
    You are an assistant for a catering company. Analyze this photo of a menu or food list table.
    
    CRITICAL INSTRUCTIONS:
    1. Extract ONLY the food dish names.
    2. Completely IGNORE quantities (e.g., '6 ltr', '10 ltr', '12 kg', '90', '55'), table headers ('Item', 'Office', 'Jafza'), dates, and order numbers.
    3. Remove unit descriptors from dish names, like '(ltr)', '(kg)', or '(Boneless)'. E.g., 'Chicken khorma (ltr)' becomes 'Chicken Khorma'.
    4. If a line contains items separated by slashes '/' (e.g., 'Letuce/Tomato/Cucumber/Radish'), SPLIT them into separate dish names, one per line.
    5. Convert all dish names to Proper Title Case (e.g., 'Papdi Chat', 'Butter Paneer').
    6. Return ONLY a plain text list with one dish name per line. No bullet points, no markdown formatting, no commentary.
    """

    # Using the updated model identifier for google-genai SDK
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[oriented_img, prompt]
    )
    
    return response.text.strip()

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
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    if st.button("✨ Extract Dish Names with Gemini AI", type="primary"):
        if not gemini_api_key:
            st.error("GEMINI_API_KEY is missing! Please add GEMINI_API_KEY to your Streamlit Cloud Secrets.")
        else:
            with st.spinner("Gemini AI is analyzing the image..."):
                try:
                    cleaned_dishes = extract_dishes_with_gemini(img, gemini_api_key)
                    st.session_state.dish_text = cleaned_dishes
                    st.success("Extraction complete!")
                except Exception as e:
                    st.error(f"Gemini Extraction Error: {str(e)}")

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
