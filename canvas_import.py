#!/usr/bin/env python3
import os
import requests
import streamlit as st

# Optional: for AI conversion if desired.
try:
    import openai
except ImportError:
    openai = None

# ---------------------------
# Configuration and Metadata
# ---------------------------
PUBLISHED = True
APP_URL = "https://ai-microapps-cimp.streamlit.app/"
# APP_IMAGE = "construct.webp"

APP_TITLE = "Construct HTML Generator"
APP_INTRO = "This micro-app allows you to convert text content into a HTML format."
APP_HOW_IT_WORKS = """
1. Fill in the details of your Canvas page.
2. Upload your document.
3. AI will convert it into HTML for you.
"""

SYSTEM_PROMPT = "Convert raw content into properly formatted HTML excluding any DOCTYPE or extraneous header lines."

# ----------------------------------------
# File Upload Text Extraction Function
# ----------------------------------------
def extract_text_from_uploaded_files(files):
    """
    Extract text from a list of uploaded files.
    Supports DOCX and PDF files. For other file types, attempts a plain text read.
    """
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
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                texts.append(text)
            except Exception as e:
                texts.append(f"[Error reading PDF: {e}]")
        else:
            try:
                texts.append(file.read().decode('utf-8'))
            except Exception as e:
                texts.append(f"[Error reading file: {e}]")
    return "\n".join(texts)

# ---------------------------
# PHASES and Fields
# ---------------------------
PHASES = {
    "generate_html": {
        "name": "Content",
        "fields": {
            "module_title": {
                "type": "text_input",
                "label": "Enter the title of your module:"
            },
            "page_title": {
                "type": "text_input",
                "label": "Enter the title of your page:"
            },
            "uploaded_files": {
                "type": "file_uploader",
                "label": "Choose files",
                "allowed_files": ['docx', 'pdf'],
                "multiple_files": True,
                "transform": extract_text_from_uploaded_files
            },
        },
        "phase_instructions": "Provide me with the content in the correct HTML format.",
        "user_prompt": [
            {
                "condition": {},
                "prompt": (
                    "I am sending you the module name: {module_title}, "
                    "page title: {page_title}, and the content extracted from the uploaded files: {uploaded_files}. "
                    "Provide this to me in properly formatted HTML format."
                )
            }
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {
    "gpt-4o": {
        "family": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
    }
}

PAGE_CONFIG = {
    "page_title": "Construct HTML Generator",
    #"page_icon": "app_images/construct.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# ---------------------------------------
# AI Conversion Function (Optional)
# ---------------------------------------
def generate_html(module_title, page_title, uploaded_text):
    """
    Uses the SYSTEM_PROMPT and the PHASES user prompt to generate HTML.
    If OPENAI_API_KEY is set, uses OpenAI; otherwise, falls back to a simple conversion.
    """
    prompt_template = PHASES["generate_html"]["user_prompt"][0]["prompt"]
    user_prompt = prompt_template.format(
        module_title=module_title,
        page_title=page_title,
        uploaded_files=uploaded_text
    )
    
    # If OpenAI is configured, use it.
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai and openai_api_key:
        openai.api_key = openai_api_key
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # or your preferred model
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            generated_html = response["choices"][0]["message"]["content"].strip()
            return generated_html
        except Exception as e:
            st.error(f"Error generating HTML via AI: {e}")
            return None
    else:
        # Fallback: wrap the extracted text in basic HTML tags.
        return f"<html><body><h3>{page_title}</h3><p>{uploaded_text}</p></body></html>"

# ---------------------------------------
# Canvas API Functions
# ---------------------------------------
def create_module(module_name, canvas_domain, course_id, headers):
    """
    Create a new module in the course.
    Returns the module ID on success.
    """
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules"
    payload = {
        "module": {
            "name": module_name,
            "published": PUBLISHED
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        module_data = response.json()
        st.info("Module created successfully!")
        return module_data["id"]
    else:
        st.error(f"Error creating module: {response.status_code} {response.text}")
        return None

def create_wiki_page(page_title, page_body, canvas_domain, course_id, headers):
    """
    Create a new wiki page in the course.
    Returns the JSON data for the page on success.
    """
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/pages"
    payload = {
        "wiki_page": {
            "title": page_title,
            "body": page_body,
            "published": PUBLISHED  # Set to False if you want the page to remain unpublished/draft
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        page_data = response.json()
        st.info("Page created successfully!")
        return page_data
    else:
        st.error(f"Error creating page: {response.status_code} {response.text}")
        return None

def add_page_to_module(module_id, page_title, page_url, canvas_domain, course_id, headers):
    """
    Add an existing wiki page to a module as a module item.
    The 'page_url' parameter should be the URL-friendly slug of the page.
    """
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules/{module_id}/items"
    payload = {
        "module_item": {
            "title": page_title,
            "type": "Page",
            "page_url": page_url,
            "published": PUBLISHED
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        st.info("Page added to module successfully!")
        return response.json()
    else:
        st.error(f"Error adding page to module: {response.status_code} {response.text}")
        return None

# ---------------------------------------
# Main Front-End using Streamlit
# ---------------------------------------
def main(config):
    # Set page configuration
    st.set_page_config(
        page_title=config["PAGE_CONFIG"]["page_title"],
        page_icon=config["page_icon"] if "page_icon" in config else None,
        layout=config["PAGE_CONFIG"]["layout"],
        initial_sidebar_state=config["PAGE_CONFIG"]["initial_sidebar_state"]
    )
    
    st.title(config["page_title"] if "page_title" in config else APP_TITLE)
    # st.image(APP_IMAGE)
    st.markdown(APP_INTRO)
    st.markdown(APP_HOW_IT_WORKS)
    
    st.header("Step 1: Provide Canvas Page Details")
    
    # Build input fields as defined in PHASES.
    module_title = st.text_input(PHASES["generate_html"]["fields"]["module_title"]["label"])
    page_title = st.text_input(PHASES["generate_html"]["fields"]["page_title"]["label"])
    uploaded_files = st.file_uploader(
        label=PHASES["generate_html"]["fields"]["uploaded_files"]["label"],
        type=PHASES["generate_html"]["fields"]["uploaded_files"]["allowed_files"],
        accept_multiple_files=PHASES["generate_html"]["fields"]["uploaded_files"]["multiple_files"]
    )
    
    # If files are uploaded, extract text.
    uploaded_text = ""
    if uploaded_files:
        uploaded_text = config["generate_html_files"] = extract_text_from_uploaded_files(uploaded_files)
        st.markdown("**Extracted Content:**")
        st.code(uploaded_text, language="text")
    
    st.header("Step 2: Generate HTML")
    if st.button("Generate HTML"):
        if not module_title or not page_title or not uploaded_text:
            st.error("Please provide all inputs (module title, page title, and upload at least one file).")
        else:
            generated_html = generate_html(module_title, page_title, uploaded_text)
            if generated_html:
                st.markdown("### Generated HTML:")
                st.code(generated_html, language="html")
                st.session_state.generated_html = generated_html
    
    st.header("Step 3: Push to Canvas")
    if "generated_html" in st.session_state:
        if st.button("Push to Canvas"):
            # Retrieve Canvas credentials from environment variables.
            canvas_domain_env = os.getenv("CANVAS_DOMAIN")
            course_id_env = os.getenv("COURSE_ID")
            access_token = os.getenv("CANVAS_ACCESS_TOKEN")
            if not canvas_domain_env or not course_id_env or not access_token:
                st.error("Missing required environment variables: CANVAS_DOMAIN, COURSE_ID, CANVAS_ACCESS_TOKEN.")
                return
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 1. Create a module.
            mod_id = create_module(module_title, canvas_domain_env, course_id_env, headers)
            if not mod_id:
                st.error("Module creation failed.")
                return
            
            # 2. Create a wiki page with the generated HTML.
            page_data = create_wiki_page(page_title, st.session_state.generated_html, canvas_domain_env, course_id_env, headers)
            if not page_data:
                st.error("Page creation failed.")
                return
            
            # 3. Add the wiki page to the module.
            page_url = page_data.get("url")
            if not page_url:
                page_url = page_title.lower().replace(" ", "-")
            add_page_to_module(mod_id, page_title, page_url, canvas_domain_env, course_id_env, headers)
    
if __name__ == "__main__":
    from core_logic.main import main as core_main  # If you have a core_logic module; otherwise, ignore.
    # Here we call our main function with the current globals as config.
    main(config=globals())
