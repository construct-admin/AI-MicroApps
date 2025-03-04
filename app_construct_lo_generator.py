import streamlit as st
import os
import hashlib

# configuration must be at the top.
st.set_page_config(
    page_title="Construct LO Generator",
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

PUBLISHED = True
APP_URL = "https://ai-microapps-ltajmcd53aypk3cp7mxsey.streamlit.app/"
APP_IMAGE = "construct.webp"

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
        {"condition": {"title_lo": True}, "prompt": "Please suggest {lo_quantity} module-learning objectives for the provided module title: {title}."},
        {"condition": {"c_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided course learning objectives: {course_lo}."},
        {"condition": {"q_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided graded assessment questions: {quiz_lo}."},
        {"condition": {"f_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided formative activity questions : {form_lo}."},
        {"condition": {"m_lo": True}, "prompt": "Please write {lo_quantity} module-learning objectives based on the provided module content: {mc_lo}."},
    ]

def get_bloom_taxonomy_conditions():
    return [
        {"condition":{},"prompt":"Please focus on the following Bloom's Taxonomy verbs: \n Verbs:"},
        {"condition": {"goal_rem": True}, "prompt": "Remember."},
        {"condition": {"goal_apply": True}, "prompt": "Apply."},
        {"condition": {"goal_evaluate": True}, "prompt": "Evaluate."},
        {"condition": {"goal_under": True}, "prompt": "Understand."},
        {"condition": {"goal_analyze": True}, "prompt": "Analyze."},
        {"condition": {"goal_create": True}, "prompt": "Create."},
        
        
    ]

def get_relevance_conditions():
    return [
        {"condition": {"real_world_relevance": True}, "prompt": "Provide module-learning objectives that are relevant to real-world practices and industry trends."},
        {"condition": {"problem_solving": True}, "prompt": "Provide module-learning objectives that focus on problem-solving and critical thinking"},
        {"condition": {"meta_cognitive_reflection": True}, "prompt": "Provide module-learning objectives that focus on meta-cognitive reflections"},
        {"condition": {"ethical_consideration": True}, "prompt": "Provide module-learning objectives that include emotional, moral, and ethical considerations."},
    ]

def get_academic_stage_conditions():
    return [
        {"condition":{},"prompt":"Please align the learning objectives to the following academic stage level: \n Level:"},    
        {"condition": {"academic_stage_radio": "Lower Primary"}, "prompt": "Lower Primary."},
        {"condition": {"academic_stage_radio": "Middle Primary"}, "prompt": "Middle Primary."},
        {"condition": {"academic_stage_radio": "Upper Primary"}, "prompt": "Upper Primary."},
        {"condition": {"academic_stage_radio": "Lower Secondary"}, "prompt": "Lower Secondary."},
        {"condition": {"academic_stage_radio": "Upper Secondary"}, "prompt": "Upper Secondary."},
        {"condition": {"academic_stage_radio": "Undergraduate"}, "prompt": "Undergraduate."},
        {"condition": {"academic_stage_radio": "Postgraduate"}, "prompt": "Postgraduate."},
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
            "m_lo": {
                "type": "checkbox",
                "label": "Provide module learning objectives based on the module description"
            },
            "c_lo": {
                "type": "checkbox",
                "label": "Provide module learning objectives based on the course learning objectives"
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
            "mc_lo": {
            "type": "text_area",
            "label": "Enter the module description",
            "height": 200,
            "showIf": {"m_lo": True}
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
                "label": "Provide learning objectives that are relevant to real-world practices and industry trends."
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
                "body": """<h3>Academic Stage</h3>""",
                "unsafe_allow_html": True
            },
            "academic_stage_radio": {
                "type": "radio",
                "label": "Select the category that best reflects the academic stage of the students.",
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

PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {"gpt-4o": {
        "family": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
    }
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
            for config in PHASES["generate_objectives"]["user_prompt"]
            if all(user_input.get(key) == value for key, value in config["condition"].items())
        ]
        return "\n".join(user_prompt_parts)
    except KeyError as e:
        raise ValueError(f"Missing key in user input: {e}")
    
### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))


# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
