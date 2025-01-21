APP_URL = "https://ptc-video-script-gen.streamlit.app/"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "PTC Video Script Generator"
APP_INTRO = """Use this application to generate PTC video scripts"""

SYSTEM_PROMPT = """Develop and support the development of high-quality academic video scripts of 780 - 880 words.

All scripts should contain the following: 
1. Hook: Start each video with something that grabs the viewer’s attention immediately. This could be a surprising fact, an intriguing question, an intriguing example, or a metaphor/analogy. The aim is to spark curiosity and encourage viewers to stay engaged. 
2. Learning Objectives: Following the hook, include 1-2 learning objectives in the video introduction. The video objectives should be aligned with Bloom´s taxonomy. 
3. Real-World Examples: Following the introductory paragraph, include a paragraph that explains the relevance of the learning material. Draw connections between the video content and real-life scenarios, or share a personal story to bring the material to life. 
4. Develop 3-4 body paragraphs 
5. Conclusion: Tie together the main points of the video and leave learners with a clear understanding of what they have learned and how they can apply it. 

Writing style and tone: 
- Writing should be clear and succinct 
- Adopt a conversational tone

The example scripts in the knowledge base and pdf should be used to inform the  tone, style, and structure of responses  
"""

RAG_IMPLEMENTATION = True  # Enable RAG integration
SOURCE_DOCUMENT = "rag_docs/PTC_Example_Pages_2_3_4.pdf"  # Path to your PDF document

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

        The PTC video script  should be aligned with the provided objectives: {learning_objectives}.
        Base the PTC video script on the following learning content: {learning_content}.
        Please align the PTC video script to the following academic stage level: {academic_stage}.
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
                "label": "Enter relevant learning content that will serve as the basis for the PTC video script.",
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
                "prompt": "The PTC video script should be aligned with the provided objectives: {learning_objectives}."
            },
            {
                "condition": {},
                "prompt": "Base the PTC video script on the following content. {learning_content}"
            },
            {
                "condition": {},
                "prompt": "Please align the PTC video script to the following academic stage level: {academic_stage_radio}."
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

# Page Configuration
PAGE_CONFIG = {
    "page_title": "Scenario Video Script Generator",
    "page_icon": "app_images/construct.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# Entry Point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
