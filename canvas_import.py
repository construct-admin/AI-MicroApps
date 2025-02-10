PUBLISHED = True
APP_URL = "https://ai-microapps-cimp.streamlit.app/"
APP_IMAGE = "construct.webp"

APP_TITLE = "Construct Canvas Page Importer"
APP_INTRO = """This micro-app allows you to import text content into Canvas LMS."""
APP_HOW_IT_WORKS = """
1. Fill in the details of your Canvas page.
2. AI will convert it into HTML for you.
3. Click "Push to Canvas" and the content will be sent to Canvas.
"""

SYSTEM_PROMPT = """Convert raw content into properly formatted HTML,
    excluding any DOCTYPE or extraneous header lines. """

# Define phases and fields
PHASES = {
    "generate_html": {
        "name": "Content",
        "fields": {
            # Input Fields
            "module_title": {
                "type": "text_input",
                "label": "Enter the title of your module:"
            },
            "page_title": {
                "type": "text_input",
                "label": "Enter the title of your page:"
            },
            "content": {
                "type": "text_area",
                "label": "Enter the content:",
                "height": 500,
            }
        },
        "phase_instructions": "Provide me with the content in the correct html format. ",
        "user_prompt": [
            {
                "condition": {},
                "prompt": """I am sending you the module name: {module_title} , page title: {page_title} and content for the page: {content}. Provide this to me in properly formatted html format."""
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
        "temperature": 0.3,
    }
}

# Page configuration
PAGE_CONFIG = {
    "page_title": "Construct LO Generator",
    "page_icon": "app_images/construct.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
