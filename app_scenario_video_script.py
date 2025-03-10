import streamlit as st
import os
import hashlib

# configuration must be at the top.
st.set_page_config(
    page_title="Scenario Video Script Generator",
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


APP_URL = "https://scenario-video-script-gen.streamlit.app/"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Scenario Video Script Generator"
APP_INTRO = """Use this application to generate scenario video scripts"""

SYSTEM_PROMPT = """Develop and refine academic video scripts for students that will support them in developing an understanding of how key academic concepts are applied in real-world practices. The academic script will be used for a scenario video.

Visuals: Incorporate visual elements that tell a story.

Output format:
Format scripts as a table, with columns for approximate time, text, and visual cues. Because we should have a change in visuals every 15 seconds, I create the script in 15 - 20-second increments, with each increment being a row in the table. You work on the assumption that each minute of video will have 120 words of text.

Scripts will include the following sections:
 1) Begin with an engaging hook. This may be a reference to a person, story, interesting statistic or case study, or a critical question from the content that should be engaged with.  Avoid pretext. Usually, we don’t need to tell them what we’re going to talk about.  We can just start talking about it. The pretext is different from a hook.  
 2) Following the introductory paragraph, add a paragraph that establishes the relevance of the learning material to real-world practices.
 3) Present the key theory or ideas of the content.
 4) Provide an explanation of how that links to solving the problems presented at the start.
 5) A conclusion that pulls the video together. The conclusion should tie together the main points explored in the script. It can be presented as key takeaways, or as though-provoking questions for reflection.
"""

RAG_IMPLEMENTATION = True  # Enable RAG integration
SOURCE_DOCUMENT = "rag_docs/ABETSIS_C1_M1_V1.pdf"  # Path to your PDF document

# Required Libraries
import os
import fitz  # PyMuPDF for PDF processing
import openai

# PDF Text Extraction Function
def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyMuPDF (fitz).
    """
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text("text")  # Extract plain text from each page
    return text

# Prompt Builder Function
def build_user_prompt(user_input):
    """
    Dynamically build the user prompt with user-provided inputs and document content.
    """
    try:
        # Retrieve user inputs
        learning_objectives = user_input.get("learning_objectives", "").strip()
        learning_content = user_input.get("learning_content", "").strip()
        academic_stage = user_input.get("academic_stage_radio", "").strip()

        # Debugging: Print retrieved values
        print("Learning Objectives:", learning_objectives)
        print("Learning Content:", learning_content)
        print("Academic Stage:", academic_stage)

        # Validate required inputs
        if not learning_objectives:
            raise ValueError("The 'Learning Objectives' field is required.")
        if not learning_content:
            raise ValueError("The 'Learning Content' field is required.")
        if not academic_stage:
            raise ValueError("An 'Academic Stage' must be selected.")

        # Load document content for RAG
        document_text = ""
        if RAG_IMPLEMENTATION and os.path.exists(SOURCE_DOCUMENT):
            document_text = extract_text_from_pdf(SOURCE_DOCUMENT)
            document_text = document_text[:2000]  # Truncate text to fit within token limits

        # Construct the user prompt
        user_prompt = f"""
        {SYSTEM_PROMPT}

        Example Template/Training Data:
        {document_text}

        The scenario video script should be aligned with the provided objectives: {learning_objectives}.
        Base the scenario video script on the following learning content: {learning_content}.
        Please align the scenario video script to the following academic stage level: {academic_stage}.
        """
        return user_prompt

    except Exception as e:
        raise ValueError(f"Error building prompt: {str(e)}")

# Configuration for the App
PHASES = {
    "generate_discussion": {
        "name": "Scenario Video Script Generator",
        "fields": {
            "learning_objectives": {
                "type": "text_area",
                "label": "Enter the relevant module-level learning objective(s):",
                "height": 500
            },
            "learning_content": {
                "type": "text_area",
                "label": "Enter relevant learning content that will serve as the basis for the scenario video script.",
                "height": 500
            },
            "academic_stage_radio": {
                "type": "radio",
                "label": "Select the academic stage of the students:",
                "options": [
                    "Lower Primary",
                    "Middle Primary",
                    "Upper Primary",
                    "Lower Secondary",
                    "Upper Secondary",
                    "Undergraduate",
                    "Postgraduate"
                ]
            }
        },
        "phase_instructions": """
        Provide the relevant details (learning objectives, content, and academic stage) to generate a discussion prompt.
        """,
        "user_prompt": [
            {
                "condition": {},
                "prompt": "The scenario video script should be aligned with the provided objectives: {learning_objectives}."
            },
            {
                "condition": {},
                "prompt": "Base the scenario video script on the following content. {learning_content}"
            },
            {
                "condition": {},
                "prompt": "Please align the scenario video script to the following academic stage level: {academic_stage_radio}."
            }
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {"gpt-4o": {
    "family": "openai",
    "model": "gpt-4o",
    "temperature": 0.5,
    "top_p": 0.9,
    "frequency_penalty": 0.5,
    "presence_penalty": 0.3
}}



SIDEBAR_HIDDEN = True

### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))

# Entry Point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
