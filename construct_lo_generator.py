PUBLISHED = True
APP_URL = "https://ai-microapps-a6qrjbdhuk5mjkkwjb3zdo.streamlit.app/"
APP_IMAGE = "construct.ico"

APP_TITLE = "Construct Learning Objectives Generator"
APP_INTRO = """This micro-app allows you to generate learning objectives or validate alignment for existing learning objectives. It streamlines instructional design by integrating AI to enhance efficiency and personalization."""
APP_HOW_IT_WORKS = """
1. Fill in the details of your course/module.
2. Configure cognitive goals and relevance preferences.
3. Generate specific, measurable, and aligned learning objectives.
"""

SYSTEM_PROMPT = """You are EduDesignGPT, an expert instructional designer specialized in creating clear, specific, and measurable module-level learning objectives for online courses."""

# Helper functions for dynamic conditions
def get_objective_prompts():
    """Generate prompts for learning objective checkboxes."""
    return [
        {"condition": {"title_lo": True}, "prompt": "Please suggest {lo_quantity} module-learning objectives for the provided course title: {title}."},
        {"condition": {"c_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided course objectives: {course_lo}."},
        {"condition": {"q_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided graded assessment questions: {quiz_lo}."},
        {"condition": {"f_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided formative activity questions: {form_lo}."},
    ]

def get_bloom_taxonomy_conditions():
    return [
        {"condition": {"goal_rem": True}, "prompt": "Include cognitive goals: Remember."},
        {"condition": {"goal_apply": True}, "prompt": "Include cognitive goals: Apply."},
        {"condition": {"goal_evaluate": True}, "prompt": "Include cognitive goals: Evaluate."},
        {"condition": {"goal_under": True}, "prompt": "Include cognitive goals: Understand."},
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
            # Request Type Selection
            "learning_obj_choices": {
                "type": "markdown",
                "body": """<h3>What would you like to do?</h3>""",
                "unsafe_allow_html": True
            },
            "title_lo": {
                "type": "checkbox",
                "label": "Suggest learning objectives based on the module title"
            },
            "c_lo": {
                "type": "checkbox",
                "label": "Provide learning objectives based on the module learning objectives"
            },
            "q_lo": {
                "type": "checkbox",
                "label": "Provide learning objectives based on the graded assessment question(s) of the module"
            },
            "f_lo": {
                "type": "checkbox",
                "label": "Provide learning objectives based on the formative activity questions of the module"
            },
            # Input Fields
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module:",
                "showIf": {"title_lo": True}
            },
            "course_lo": {
                "type": "text_area",
                "label": "Enter the course learning objective:",
                "height": 300,
                "showIf": {"c_lo": True}
            },
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s):",
                "height": 300,
                "showIf": {"q_lo": True}
            },
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity question(s):",
                "height": 300,
                "showIf": {"f_lo": True}
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3
            },
            # Relevance Preferences
            "relevance_preferences": {
                "type": "markdown",
                "body": """<h3>Preferences:</h3> Select additional focus areas for your learning objectives.""",
                "unsafe_allow_html": True
            },
            "real_world_relevance": {
                "type": "checkbox",
                "label": "Try to provide learning objectives that are relevant to real-world practices and industry trends."
            },
            "problem_solving": {
                "type": "checkbox",
                "label": "Focus on problem-solving and critical thinking."
            },
            "meta_cognitive_reflection": {
                "type": "checkbox",
                "label": "Focus on meta-cognitive reflections."
            },
            "ethical_consideration": {
                "type": "checkbox",
                "label": "Include emotional, moral, and ethical considerations."
            },
            # Bloom's Taxonomy
            "bloom_taxonomy": {
                "type": "markdown",
                "body": """<h3>Bloom's Taxonomy</h3> Select cognitive goals to focus on:""",
                "unsafe_allow_html": True
            },
            "goal_rem": {
                "type": "checkbox",
                "label": "Remember"
            },
            "goal_apply": {
                "type": "checkbox",
                "label": "Apply"
            },
            "goal_evaluate": {
                "type": "checkbox",
                "label": "Evaluate"
            },
            "goal_under": {
                "type": "checkbox",
                "label": "Understand"
            },
            "goal_analyze": {
                "type": "checkbox",
                "label": "Analyze"
            },
            "goal_create": {
                "type": "checkbox",
                "label": "Create"
            },
            # Academic Stage
            "academic_stage": {
            "type": "markdown",
            "label": """<h3>Academic Stage</h3> Select the category that best reflects the academic stage of the students.""",
            "unsafe_allow_html" :True
            },
            "lower_primary": {
                "type": "radio",
                "label": "Lower Primary",
            },
            "middle_primary": {
                "type": "radio",
                "label": "Middle Primary",
            },
            "upper_primary": {
                "type": "radio",
                "label": "Upper Primary",
            },
            "lower_secondary": {
                "type": "radio",
                "label": "Lower Secondary",
            },
            "upper_secondary": {
                "type": "radio",
                "label": "Upper Secondary",
            },
            "undergraduate": {
                "type": "radio",
                "label": "Undergraduate",
            }
            ,
            "postgraduate": {
                "type": "radio",
                "label": "Postgraduate",
            }
        },
        "phase_instructions": """
        Dynamically build the user prompt based on:
        - Selected checkboxes (e.g., title, course objectives, assessments).
        - Preferences for relevance, Bloom's Taxonomy goals, and academic stages.
        """,
        "user_prompt": (
            get_objective_prompts()
            + get_relevance_conditions()
            + get_bloom_taxonomy_conditions()
            + get_academic_stage_conditions()
        ),
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Page configuration
PAGE_CONFIG = {
    "page_title": "Construct LO Generator",
    "page_icon": "️app_images\construct.ico",
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
