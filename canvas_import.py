PUBLISHED = True
APP_URL = "https://ai-microapps-cimp.streamlit.app/"
APP_IMAGE = "construct.webp"

APP_TITLE = "Construct HTML Generator"
APP_INTRO = "This micro-app allows you to convert text content into a HTML format."
APP_HOW_IT_WORKS = """
1. Fill in the details of your Canvas page.
2. Upload your document.
3. AI will convert it into HTML for you.
"""

SYSTEM_PROMPT = "Convert raw content into properly formatted HTML excluding any DOCTYPE or extraneous header lines."

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
                # Make sure to add 'python-docx' to your requirements file
                from docx import Document
                doc = Document(file)
                full_text = "\n".join([para.text for para in doc.paragraphs])
                texts.append(full_text)
            except Exception as e:
                texts.append(f"[Error reading DOCX: {e}]")
        elif ext == 'pdf':
            try:
                # Use pypdf (already in your requirements)
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
                # For other file types, attempt to read as plain text
                texts.append(file.read().decode('utf-8'))
            except Exception as e:
                texts.append(f"[Error reading file: {e}]")
    return "\n".join(texts)

# Define phases and fields
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
                # The transform function converts the raw file upload into extracted text.
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

# Page configuration
PAGE_CONFIG = {
    "page_title": "Construct HTML Generator",
    "page_icon": "app_images/construct.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
