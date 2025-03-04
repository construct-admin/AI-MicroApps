import streamlit as st
import os
import hashlib

# configuration must be at the top.
st.set_page_config(
    page_title="Text from Image Generator",
    page_icon="app_images/construct.webp",
    layout="centered",
    initial_sidebar_state="expanded"
)

### hash code function for the encryption
def hash_code(input_code):
    """Hashes the access code using SHA-256."""
    return hashlib.sha256(input_code.encode()).hexdigest()

### retrieve hash code 
ACCESS_CODE_HASH = os.getenv("ACCESS_CODE_HASH")

if not ACCESS_CODE_HASH:
    st.error("⚠️ Hashed access code not found. Please set ACCESS_CODE_HASH.")
    st.stop()

### Authentication Logic
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Access Restricted")
    access_code_input = st.text_input("Enter Access Code:", type="password")

    if st.button("Submit"):
        if hash_code(access_code_input) == ACCESS_CODE_HASH:
            st.session_state.authenticated = True
            st.rerun() 
        else:
            st.error("Incorrect access code. Please try again.")

    st.stop()  # Prevent unauthorized access


### Main Application Configurations
APP_URL = "https://image-text-gen.streamlit.app/"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Text from Image Generator"
APP_INTRO = "This application accepts images via upload and returns the text featured within the image."

APP_HOW_IT_WORKS = """
This app generates the text from images. 
For most images, it provides the text featured within an image.
"""

SHARED_ASSET = {}
HTML_BUTTON = {}

SYSTEM_PROMPT = "You accept app_images in file format and extract the text from images exactly as it appears (verbatim)."

PHASES = {
    "phase1": {
        "name": "Image Input and Text Generation",
        "fields": {
            "uploaded_files": {
                "type": "file_uploader",
                "label": "Choose files",
                "allowed_files": ['png', 'jpeg', 'gif', 'webp'],
                "multiple_files": True,
            },
        },
        "phase_instructions": "Generate the exact text from the image uploads",
        "user_prompt": [
            {
                "condition": {},
                "prompt": """I am sending you one or more app_images. Please provide separate text for each image I send. The text should:
                - extract text from the images exactly as it appears (verbatim)"""
            }
        ],
        "show_prompt": True,
        "allow_skip": False,
        "ai_response": True,
        "allow_revisions": True,
    }
}
PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {
    "temperature": 0.3
}

SCORING_DEBUG_MODE = True
DISPLAY_COST = True

COMPLETION_MESSAGE = "Thanks for using the text generation service"
COMPLETION_CELEBRATION = False

SIDEBAR_HIDDEN = True

### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
