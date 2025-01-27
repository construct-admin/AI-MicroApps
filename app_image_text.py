APP_URL = "https://image-text-gen.streamlit.app/" 
APP_IMAGE = "construct.webp" 
PUBLISHED = True # Status of the app

APP_TITLE = "Text from Image Generator"
APP_INTRO = "This app accepts images via upload and returns the text featured within the image."

APP_HOW_IT_WORKS = """
This app generates the text from images. 
                For most images, it provides the text featured within an image.
 """

SHARED_ASSET = {
}

HTML_BUTTON = {

}

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

PAGE_CONFIG = {
    "page_title": "Text from Image Generator",
    "page_icon": "app_images/construct.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
