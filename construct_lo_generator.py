PUBLISHED = True
APP_URL = "https://lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Generator"
APP_INTRO = """This micro-app allows you to generate learning objectives or validate alignment for existing learning objectives. It streamlines instructional design by integrating AI to enhance efficiency and personalization."""
APP_HOW_IT_WORKS = """
1. Fill in the details of your course/module.
2. Configure cognitive goals and relevance preferences.
3. Generate specific, measurable, and aligned learning objectives.
"""

SYSTEM_PROMPT = """You are EduDesignGPT, an expert instructional designer specialized in creating clear, specific, and measurable module-level learning objectives for online courses."""

# Helper functions for dynamic conditions
def get_bloom_taxonomy_conditions():
    return [
        {"condition": {"goal_apply": True}, "prompt": "Include cognitive goals: Apply."},
        {"condition": {"goal_evaluate": True}, "prompt": "Include cognitive goals: Evaluate."},
        {"condition": {"goal_analyze": True}, "prompt": "Include cognitive goals: Analyze."},
        {"condition": {"goal_create": True}, "prompt": "Include cognitive goals: Create."},
    ]

def get_relevance_conditions():
    return [
        {"condition": {"real_world_relevance": True}, "prompt": "Try to provide learning objectives that are relevant to real-world practices and industry trends."},
        {"condition": {"problem_solving": True}, "prompt": "Focus on problem-solving and critical thinking."},
        {"condition": {"meta_cognitive_reflection": True}, "prompt": "Focus on meta-cognitive reflections."},
        {"condition": {"ethical_consideration": True}, "prompt": "Include emotional, moral, and ethical considerations."},
    ]

def get_academic_stage_conditions():
    return [
        {"condition": {"lower_primary": True}, "prompt": "Target the academic stage: Lower Primary."},
        {"condition": {"middle_primary": True}, "prompt": "Target the academic stage: Middle Primary."},
        {"condition": {"upper_primary": True}, "prompt": "Target the academic stage: Upper Primary."},
        {"condition": {"lower_secondary": True}, "prompt": "Target the academic stage: Lower Secondary."},
        {"condition": {"upper_secondary": True}, "prompt": "Target the academic stage: Upper Secondary."},
        {"condition": {"undergraduate": True}, "prompt": "Target the academic stage: Undergraduate."},
        {"condition": {"postgraduate": True}, "prompt": "Target the academic stage: Postgraduate."},
    ]

# Define phases and fields
PHASES = {
    "generate_objectives": {
        "name": "Generate Learning Objectives",
        "fields": {
            "request_type": {
                "type": "radio",
                "label": "What would you like to do?",
                "options": [
                    "Suggest learning objectives based on the title",
                    "Provide learning objectives based on the course learning objectives",
                    "Provide learning objectives based on the graded assessment question(s) of the module",
                    "Provide learning objectives based on the formative activity questions"
                ]
            },
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module:",
                "showIf": {"request_type": ["Suggest learning objectives based on the title"]}
            },
            "course_lo": {
                "type": "text_area",
                "label": "Enter the course learning objective:",
                "showIf": {"request_type": ["Provide learning objectives based on the course learning objectives"]},
                "height": 300
            },
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s):",
                "showIf": {"request_type": ["Provide learning objectives based on the graded assessment question(s) of the module"]},
                "height": 300
            },
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity question(s):",
                "showIf": {"request_type": ["Provide learning objectives based on the formative activity questions"]},
                "height": 300
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3
            },
        },
        "phase_instructions": """
        Dynamically build the user prompt based on:
        - Request type (e.g., title, course objectives, assessments).
        - Preferences for relevance, Bloom's Taxonomy goals, and academic stages.
        """,
        "user_prompt": [
            {"condition": {"request_type": "Suggest learning objectives based on the title"}, "prompt": "Please suggest {lo_quantity} learning objectives for the provided course title: {title}."},
            {"condition": {"request_type": "Provide learning objectives based on the course learning objectives"}, "prompt": "Please write {lo_quantity} learning objectives based on the provided course objectives: {course_lo}."},
            {"condition": {"request_type": "Provide learning objectives based on the graded assessment question(s) of the module"}, "prompt": "Please write {lo_quantity} learning objectives based on the provided graded assessment questions: {quiz_lo}."},
            {"condition": {"request_type": "Provide learning objectives based on the formative activity questions"}, "prompt": "Please write {lo_quantity} learning objectives based on the provided formative assessment questions: {form_lo}."},
        ] + get_relevance_conditions() + get_bloom_taxonomy_conditions() + get_academic_stage_conditions(),
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Page configuration
PAGE_CONFIG = {
    "page_title": "LO Generator",
    "page_icon": "️🔹",
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
            config["prompt"].format(**user_input)
            for config in PHASES["generate_objectives"]["user_prompt"]
            if all(user_input.get(key) == value for key, value in config["condition"].items())
        ]
        return "\n".join(user_prompt_parts)
    except KeyError as e:
        raise ValueError(f"Missing key in user input: {e}")

# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
