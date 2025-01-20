APP_URL = "https://discussion.streamlit.app"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Discussion Generator"
APP_INTRO = """Use this application to generate discussion forum questions."""

SYSTEM_PROMPT = """You are a discussion generator. Your goal is to develop structured discussion board prompts for online courses that align with user-provided learning objectives or content.

All discussion board prompts should contain the following:
1. **Discussion Questions**: Develop focused, open-ended questions that promote analysis and higher-order thinking. Include no more than 2 questions.
2. **Discussion Instructions**: Include:
   - Word count guidelines (e.g., initial post no more than 250 words).
   - Encouragement for learners to use personal experiences and academic references.
   - Instructions to respond to peers constructively while maintaining respect and professionalism.
3. **Conclusion**: Tie together the main points of the discussion and leave learners with a clear takeaway.

**Writing Style and Tone**:
- Writing should be clear, concise, and conversational.
- Use active voice.

"""

# Define phases and fields
PHASES = {
    "generate_discussion": {
        "name": "Generate Discussion Prompt",
        "fields": {
            "learning_objectives": {
                "type": "text_area",
                "label": "Enter the relevant module-level learning objective(s):",
                "height": 300
            },
            "learning_content": {
                "type": "text_area",
                "label": "Enter the relevant learning content:",
                "height": 300
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
                "condition": {"learning_objectives": True},
                "prompt": "Generate a discussion prompt aligned with the following learning objective: {learning_objectives}."
            },
            {
                "condition": {"learning_content": True},
                "prompt": "Generate a discussion prompt aligned with the following learning content: {learning_content}."
            },
            {
                "condition": {"academic_stage_radio": True},
                "prompt": "Please align the learning objectives to the following academic stage level: {academic_stage_radio}"
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
        "top_p": 0.85,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1
    }
}

# Page configuration
PAGE_CONFIG = {
    "page_title": "Discussion Prompt Generator",
    "page_icon": "app_images/discussion_generator.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# Prompt builder
def build_user_prompt(user_input):
    """
    Build the user prompt dynamically based on user input.
    """
    try:
        user_prompt_parts = [
            config["prompt"].format(**{key: user_input.get(key, "") for key in config["condition"].keys()})
            for config in PHASES["generate_discussion"]["user_prompt"]
            if all(user_input.get(key) == value for key, value in config["condition"].items())
        ]
        return "\n".join(user_prompt_parts)
    except KeyError as e:
        raise ValueError(f"Missing key in user input: {e}")

# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())