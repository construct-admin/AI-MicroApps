import streamlit as st
import os
import hashlib

st.set_page_config(
    page_title="Alt Text Generator",
    page_icon="app_images/construct.webp",
    layout="centered",
    initial_sidebar_state="expanded"
)

### Hash function for access code encryption
def hash_code(input_code):
    """Hashes the access code using SHA-256."""
    return hashlib.sha256(input_code.encode()).hexdigest()

### Retrieve hash code from environment variable
ACCESS_CODE_HASH = os.getenv("ACCESS_CODE_HASH")

if not ACCESS_CODE_HASH:
    st.error("⚠️ Hashed access code not found. Please set ACCESS_CODE_HASH.")
    st.stop()

### Authentication Logic
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Access Restricted")
    access_code_input = st.text_input("Enter Access Code:", type="password", key="access_code_input")

    if st.button("Submit", key="submit_access_code"):
        if hash_code(access_code_input) == ACCESS_CODE_HASH:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect access code. Please try again.")

    st.stop()  # Prevent unauthorized access

### App Info
APP_URL = "https://alt-text-bot.streamlit.app/"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Alt Text Generator"
APP_INTRO = "This app accepts uploaded images and returns alt text for accessibility."

APP_HOW_IT_WORKS = """
This app creates alt text for accessibility from images. 
For most images, it provides brief alt text to describe the image, focusing on the most important information first. 

For complex images, like charts and graphs, the app creates a short description of the image and a longer detail that describes what the complex image is conveying. 

For more information, see <a href="https://www.w3.org/WAI/tutorials/images/" target="_blank">W3C Images Accessibility Guidelines</a>.
"""

### System Configurations
SYSTEM_PROMPT = "You accept images in URL and file format to generate description or alt text according to WCAG 2.2 AA accessibility standards."

PHASES = {
    "phase1": {
        "name": "Image Input and Alt Text Generation",
        "fields": {
            "uploaded_files": {
                "type": "file_uploader",
                "label": "Choose files",
                "allowed_files": ['png', 'jpeg', 'gif', 'webp'],
                "multiple_files": True,
                "key": "file_uploader"
            },
            "important_text": {
                "type": "checkbox",
                "label": "The text in my image(s) is important",
                "value": False,
                "help": "If text is important, it should be included in the alt text. If it is irrelevant or covered in text elsewhere on the page, it should not be included",
                "key": "important_text_checkbox"
            },
            "complex_image": {
                "type": "checkbox",
                "label": "My image is a complex image (chart, infographic, etc...)",
                "value": False,
                "help": "Complex images get both a short and a long description of the image",
                "key": "complex_image_checkbox"
            }
        },
        "phase_instructions": "Generate the alt text for the image URLs and uploads",
        "user_prompt": [
            {
                "condition": {"important_text": False, "complex_image": False},
                "prompt": """I am sending you one or more images. Please provide separate appropriate alt text for each image I send. The alt text should:
                - Describe the most important concept displayed in the image in less than 120 characters."""
            },
            {
                "condition": {"complex_image": True},
                "prompt": """I am sending you one or more complex images. Please provide a short description of the most important concept depicted in the image; and a long description to explain the relationship between components and transcribe text verbatim to provide a detailed and informative description of the image. 

                **Format your output as follows:**  
                **Short Description:**  
                [Short Description]  

                **Long Description:**  
                [Long Description]  
                """
            },
            {
                "condition": {"important_text": True, "complex_image": False},
                "prompt": """I am sending you one or more images. Please provide separate appropriate alt text for each image I send. The alt text should:
                - Describe the most important concept displayed in the image in less than 120 characters.  
                - Transcribe text verbatim to provide a detailed and informative description of the image."""
            },
            {
                "condition": {"important_text": True, "complex_image": True},
                "prompt": """I am sending you one or more complex images. Please provide separate appropriate alt text for each image I send. The alt text should:
                - Describe the most important concept displayed in the image in less than 120 characters.  
                - The long description should explain the relationship between parts and transcribe text verbatim to provide a detailed and informative description of the image.  

                **Format your output as follows:**  
                **Short Description:**  
                [Short Description]  

                **Long Description:**  
                [Long Description]  
                """
            },
            {
                "condition": {},
                "prompt": "Here are the uploaded images - {http_img_urls} and uploaded files."
            }
        ],
        "show_prompt": True,
        "allow_skip": False,
    }
}

### Preferred Model Configuration
PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {
    "temperature": 1.0
}

SCORING_DEBUG_MODE = True
DISPLAY_COST = True

COMPLETION_MESSAGE = "Thanks for using the Alt Text Generator service"
COMPLETION_CELEBRATION = False

SIDEBAR_HIDDEN = True

### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}), key="logout_button")

from core_logic.main import main

if __name__ == "__main__":
    main(config=globals())
