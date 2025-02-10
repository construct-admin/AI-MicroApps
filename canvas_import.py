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
# APP_IMAGE = "construct.webp"  # Uncomment and adjust if you want to display an image

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
# PHASES and Fields (Dictionary Approach)
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
    # "page_icon": "app_images/construct.webp",  # Uncomment if you have an image asset
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# ---------------------------------------
# New Prompt Generation (No AI Call)
# ---------------------------------------
def generate_user_prompt(module_title, page_title, uploaded_text):
    """
    Uses the PHASES user prompt template to generate a prompt string.
    This string is displayed in a copyable format and stored in a variable.
    """
    prompt_template = PHASES["generate_html"]["user_prompt"][0]["prompt"]
    final_prompt = prompt_template.format(
        module_title=module_title,
        page_title=page_title,
        uploaded_files=uploaded_text
    )
    return final_prompt

def build_user_prompt(user_input):
    """
    Build the user prompt dynamically based on user input.
    Uses the prompt template from PHASES["generate_html"]["user_prompt"].
    """
    try:
        user_prompt_parts = [
            config["prompt"].format(**{key: user_input.get(key, "") 
                                       for key in config.get("condition", {}).keys()})
            for config in PHASES["generate_html"]["user_prompt"]
            if all(user_input.get(key, "") == value 
                   for key, value in config.get("condition", {}).items())
        ]
        return "\n".join(user_prompt_parts)
    except KeyError as e:
        raise ValueError(f"Missing key in user input: {e}")

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
    st.set_page_config(
        page_title=config["PAGE_CONFIG"]["page_title"],
        page_icon=config.get("page_icon", None),
        layout=config["PAGE_CONFIG"]["layout"],
        initial_sidebar_state=config["PAGE_CONFIG"]["initial_sidebar_state"]
    )
    
    st.title(config.get("page_title", APP_TITLE))
    # st.image(APP_IMAGE)  # Uncomment if you want to display an image.
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
        uploaded_text = extract_text_from_uploaded_files(uploaded_files)
        st.markdown("**Extracted Content:**")
        st.code(uploaded_text, language="text")
    
    st.header("Step 2: Generate User Prompt")
    if st.button("Generate Prompt"):
        if not module_title or not page_title or not uploaded_text:
            st.error("Please provide all inputs (module title, page title, and upload at least one file).")
        else:
            final_user_prompt = generate_user_prompt(module_title, page_title, uploaded_text)
            st.markdown("### Generated User Prompt:")
            st.code(final_user_prompt, language="text")  # Display in a copyable format
            st.session_state.final_user_prompt = final_user_prompt
    
    st.header("Step 3: Push to Canvas")
    if "final_user_prompt" in st.session_state:
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
            
            # 2. Create a wiki page with the generated user prompt.
            # (Here, we are using the generated user prompt as the page body.)
            page_data = create_wiki_page(page_title, st.session_state.final_user_prompt, canvas_domain_env, course_id_env, headers)
            if not page_data:
                st.error("Page creation failed.")
                return
            
            # 3. Add the wiki page to the module.
            page_url = page_data.get("url")
            if not page_url:
                page_url = page_title.lower().replace(" ", "-")
            add_page_to_module(mod_id, page_title, page_url, canvas_domain_env, course_id_env, headers)
    
if __name__ == "__main__":
    try:
        from core_logic.main import main as core_main  # Optional: if you have a core_logic module.
    except ImportError:
        pass
    main(config=globals())
