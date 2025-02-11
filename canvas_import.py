#!/usr/bin/env python3
import os
import requests
import streamlit as st

# Optional: for AI conversion if desired (not used in this version).
try:
    import openai
except ImportError:
    openai = None

# ---------------------------
# Configuration and Metadata
# ---------------------------
PUBLISHED = True
APP_URL = "https://alt-text-bot.streamlit.app/"

APP_TITLE = "Construct HTML Generator"
APP_INTRO = "This micro-app allows you to convert text content into HTML format."
APP_HOW_IT_WORKS = """
1. Fill in the details of your Canvas page.
2. Upload your document (DOCX or PDF).
3. The app will generate a user prompt (copyable) that includes the module name, page title, and the extracted content.
   You can then use that prompt as part of your system prompt.
"""

SYSTEM_PROMPT = "Convert raw content into properly formatted HTML excluding any DOCTYPE or extraneous header lines."

# ----------------------------------------
# File Upload Text Extraction Function
# ----------------------------------------
def extract_text_from_uploaded_files(files):
    """Extract text from DOCX and PDF files."""
    texts = []
    for file in files:
        ext = file.name.split('.')[-1].lower()
        if ext == 'docx':
            try:
                from docx import Document
                doc = Document(file)
                full_text = "\n".join([para.text for para in doc.paragraphs])
                texts.append(full_text)
            except Exception as e:
                texts.append(f"[Error reading DOCX: {e}]")
        elif ext == 'pdf':
            try:
                from pypdf import PdfReader
                pdf = PdfReader(file)
                text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                texts.append(text)
            except Exception as e:
                texts.append(f"[Error reading PDF: {e}]")
        else:
            try:
                texts.append(file.read().decode('utf-8'))
            except Exception as e:
                texts.append(f"[Error reading file: {e}]")
    return "\n".join(texts)

# ---------------------------------------
# OpenAI API Call Function
# ---------------------------------------
def get_ai_generated_html(prompt):
    """Calls OpenAI API to format extracted content into HTML."""
    openai_api_key = st.secrets["OPENAI_API_KEY"]  
    if not openai_api_key:
        st.error("Missing OpenAI API Key. Please add it to your Streamlit secrets.")
        return None

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip("`")  # Strip any ```
    else:
        st.error(f"OpenAI API Error: {response.status_code} - {response.text}")
        return None

# ---------------------------------------
# Canvas API Functions
# ---------------------------------------
def create_module(module_name, canvas_domain, course_id, headers):
    """Create a new module in the course and return its ID."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules"
    payload = {"module": {"name": module_name, "published": PUBLISHED}}
    response = requests.post(url, headers=headers, json=payload)
    return response.json().get("id") if response.status_code in [200, 201] else None

def create_wiki_page(page_title, page_body, canvas_domain, course_id, headers):
    """Create a new wiki page in the Canvas course."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/pages"
    payload = {"wiki_page": {"title": page_title, "body": page_body, "published": PUBLISHED}}
    response = requests.post(url, headers=headers, json=payload)
    return response.json() if response.status_code in [200, 201] else None

def add_page_to_module(module_id, page_title, page_url, canvas_domain, course_id, headers):
    """Add an existing wiki page to a module."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules/{module_id}/items"
    payload = {"module_item": {"title": page_title, "type": "Page", "page_url": page_url, "published": PUBLISHED}}
    return requests.post(url, headers=headers, json=payload).json()

# ---------------------------------------
# Main Front-End using Streamlit
# ---------------------------------------
def main():
    st.set_page_config(page_title="Construct HTML Generator", layout="centered", initial_sidebar_state="expanded")
    
    st.title(APP_TITLE)
    st.markdown(APP_INTRO)
    st.markdown(APP_HOW_IT_WORKS)
    
    st.header("Step 1: Provide Canvas Page Details")
    
    module_title = st.text_input("Enter the title of your module:")
    page_title = st.text_input("Enter the title of your page:")
    uploaded_files = st.file_uploader("Choose files", type=['docx', 'pdf'], accept_multiple_files=True)
    
    uploaded_text = extract_text_from_uploaded_files(uploaded_files) if uploaded_files else ""
    
    if uploaded_text:
        st.markdown("**Extracted Content:**")
        st.text_area("Extracted Text", uploaded_text, height=300)

    st.header("Step 2: Generate HTML")
    if st.button("Generate HTML"):
        if not module_title or not page_title or not uploaded_text:
            st.error("Please provide all inputs (module title, page title, and upload at least one file).")
        else:
            prompt = f"Module: {module_title}\nPage Title: {page_title}\nContent: {uploaded_text}"
            ai_generated_html = get_ai_generated_html(prompt)

            if ai_generated_html:
                st.markdown("### AI-Generated HTML Output:")
                st.text_area("AI Response:", ai_generated_html, height=300)
                st.session_state.ai_generated_html = ai_generated_html
            else:
                st.error("AI failed to generate HTML content.")

    st.header("Step 3: Push to Canvas")
    if "ai_generated_html" in st.session_state and st.session_state.ai_generated_html:
        if st.button("Push to Canvas"):
            canvas_domain_env = st.secrets["CANVAS_DOMAIN"]
            course_id_env = st.secrets["CANVAS_ID"]
            access_token = st.secrets["CANVAS_ACCESS_TOKEN"]

            if not canvas_domain_env or not course_id_env or not access_token:
                st.error("Missing required environment variables.")
                return
            
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            mod_id = create_module(module_title, canvas_domain_env, course_id_env, headers)
            if not mod_id:
                st.error("Module creation failed.")
                return

            page_data = create_wiki_page(page_title, st.session_state.ai_generated_html, canvas_domain_env, course_id_env, headers)
            if not page_data:
                st.error("Page creation failed.")
                return

            page_url = page_data.get("url") or page_title.lower().replace(" ", "-")
            add_page_to_module(mod_id, page_title, page_url, canvas_domain_env, course_id_env, headers)

if __name__ == "__main__":
    main()