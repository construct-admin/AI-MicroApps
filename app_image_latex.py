import streamlit as st
import os
import hashlib

# configuration must be at the top.
st.set_page_config(
    page_title="LaTeX Generator",
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



APP_URL = "https://image-late-gen.streamlit.app/" 
APP_IMAGE = "construct.webp" 
PUBLISHED = True # Status of the app

APP_TITLE = "LaTex Generator"
APP_INTRO = "This app accepts uploaded images and returns LaTeX code."

APP_HOW_IT_WORKS = """
This app creates LaTeX code from images. 
                For most images, it provides properly formated LaTeX code.
 """

SHARED_ASSET = {
}

HTML_BUTTON = {

}

SYSTEM_PROMPT = """You accept images in url and file format containing mathematical equations, symbols, and text into accurate and you convert the images into properly formatted LaTeX code in MathJax. Output: Provide the final LaTeX (MathJax) code in a format that can be easily copied or exported.
### Output Requirements:
1. **Use `\dfrac{}` instead of `\frac{}`** when dealing with nested fractions for better readability.
2. **Ensure proper spacing** using `\,`, `\quad`, or `{}` where necessary.
3. **Avoid missing multipliers** like implicit multiplication (`\cdot`).
4. **Return only the LaTeX code** inside `$$` or `\[\]` for easy export.

### Example Output Format:
```latex
Re = 2 \dfrac{\dfrac{1}{2} \rho v_{\infty}^2 A}{\mu \dfrac{v_{\infty}}{l} A}"""

PHASES = {
    "phase1": {
        "name": "Image Input and LaTeX Generation",
        "fields": {
            "uploaded_files": {
                "type": "file_uploader",
                "label": "Choose files",
                "allowed_files": ['png', 'jpeg', 'gif', 'webp'],
                "multiple_files": True,
            },
        },
       "phase_instructions": "Generate LaTeX for the image urls and uploads",
        "user_prompt": [
            {
                "condition": {},
                "prompt": """I am sending you one or more app_images. Please provide separate LaTeX (MathJax) code for each image I send. The LaTeX (MathJax) code should:
                - convert the images into properly formatted LaTeX code in MathJax exactly as it appears (verbatim)"""
            }
        ],
        "show_prompt": True,
        "allow_skip": False,
        "ai_response": True,
        "allow_revisions": True,
    }
}
PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {}

SCORING_DEBUG_MODE = True
DISPLAY_COST = True

COMPLETION_MESSAGE = "Thanks for using the LaTeX Generator service"
COMPLETION_CELEBRATION = False

SIDEBAR_HIDDEN = True

### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
