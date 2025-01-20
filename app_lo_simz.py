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

PHASES = {
    "generate_objectives": {
        "name": "Generate Learning Objectives",
        "fields": {
            "request_type": {
                "type": "checkbox",
                "label": "What would you like to do?",
                "options": [
                    "Suggest learning objectives based on the title",
                    "Provide learning objectives based on the course learning objectives",
                    "Provide learning objectives based on the graded assessment question(s) of the module",
                    "Provide learning objectives based on the formative activity questions"
                ],
            },
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module:",
                #"showIf": {"request_type": ["Suggest learning objectives based on the title"]}
            },
            "course_lo": {
                "type": "text_area",
                "label": "Enter the course learning objective:",
                #"showIf": {"request_type": ["Provide learning objectives based on the course learning objectives"]},
                "height": 300
            },
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s):",
                #"showIf": {"request_type": ["Provide learning objectives based on the graded assessment question(s) of the module"]},
                "height": 300
            },
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity question(s):",
                #"showIf": {"request_type": ["Provide learning objectives based on the formative activity questions"]},
                "height": 300
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3
            },
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
            "bloom_taxonomy": {
                "type": "markdown",
                "body": """<h3>Bloom's Taxonomy</h3> Select cognitive goals to focus on:""",
                "unsafe_allow_html": True
            },
            "goal_apply": {
                "type": "checkbox",
                "label": "Apply"
            },
            "goal_evaluate": {
                "type": "checkbox",
                "label": "Evaluate"
            },
            "goal_analyze": {
                "type": "checkbox",
                "label": "Analyze"
            },
            "goal_create": {
                "type": "checkbox",
                "label": "Create"
            },
            "academic_stage": {
                "type": "markdown",
                "body": """<h3>Academic Stage:</h3> Select the category that best reflects the academic stage of the students.""",
                "unsafe_allow_html": True
            },
            "lower_primary": {
                "type": "checkbox",
                "label": "Lower Primary"
            },
            "middle_primary": {
                "type": "checkbox",
                "label": "Middle Primary"
            },
            "upper_primary": {
                "type": "checkbox",
                "label": "Upper Primary"
            },
            "lower_secondary": {
                "type": "checkbox",
                "label": "Lower Secondary"
            },
            "upper_secondary": {
                "type": "checkbox",
                "label": "Upper Secondary"
            },
            "undergraduate": {
                "type": "checkbox",
                "label": "Undergraduate"
            },
            "postgraduate": {
                "type": "checkbox",
                "label": "Postgraduate"
            }
        },
                "phase_instructions": """
        Build the user prompt based on the following conditions:
        - If the request type is 'Suggest learning objectives based on the title,' include the title and number of objectives.
        - If the request type is 'Provide learning objectives based on the course learning objectives,' include the provided course objectives.
        - Append relevance preferences, problem-solving, meta-cognitive reflections, and ethical considerations if selected.
        - Include specific Bloom's Taxonomy goals if checked (e.g., Apply, Evaluate).
        - Specify academic stages if selected (e.g., Lower Primary, Undergraduate).
        """,
        "user_prompt": [
            {
                "condition": {"request_type": "Suggest learning objectives based on the title"},
                "prompt": "Please suggest {lo_quantity} learning objectives for the provided course title: {title}.",
            },
            {
                "condition": {"request_type": "Provide learning objectives based on the course learning objectives"},
                "prompt": "Please write {lo_quantity} learning objectives based on the provided course objectives: {course_lo}.",
            },
            {
                "condition": {"request_type": "Provide learning objectives based on the graded assessment question(s) of the module"},
                "prompt": "Please write {lo_quantity} learning objectives based on the provided graded assessment questions: {quiz_lo}.",
            },
             {
                "condition": {"request_type": "Provide learning objectives based on the formative activity questions"},
                "prompt": "Please write {lo_quantity} learning objectives based on the provided graded assessment questions: {form_lo}.",
            },
            {
                "condition": {"real_world_relevance": True},
                "prompt": "Try to provide learning objectives that are relevant to real-world practices and industry trends.",
            },
            {
                "condition": {"problem_solving": True},
                "prompt": "Focus on problem-solving and critical thinking.",
            },
            {
                "condition": {"meta_cognitive_reflection": True},
                "prompt": "Focus on meta-cognitive reflections.",
            },
            {
                "condition": {"ethical_consideration": True},
                "prompt": "Include emotional, moral, and ethical considerations.",
            },
            {
                "condition": {"goal_apply": True},
                "prompt": "Include cognitive goals: Apply.",
            },
            {
                "condition": {"goal_evaluate": True},
                "prompt": "Include cognitive goals: Evaluate.",
            },
            {
                "condition": {"goal_analyze": True},
                "prompt": "Include cognitive goals: Analyze.",
            },
            {
                "condition": {"goal_create": True},
                "prompt": "Include cognitive goals: Create.",
            },
            {
                "condition": {"lower_primary": True},
                "prompt": "Target the academic stage: Lower Primary.",
            },
            {
                "condition": {"middle_primary": True},
                "prompt": "Target the academic stage: Middle Primary.",
            },
            {
                "condition": {"upper_primary": True},
                "prompt": "Target the academic stage: Upper Primary.",
            },
            {
                "condition": {"lower_secondary": True},
                "prompt": "Target the academic stage: Lower Secondary.",
            },
            {
                "condition": {"upper_secondary": True},
                "prompt": "Target the academic stage: Upper Secondary.",
            },
            {
                "condition": {"undergraduate": True},
                "prompt": "Target the academic stage: Undergraduate.",
            },
            {
                "condition": {"postgraduate": True},
                "prompt": "Target the academic stage: Postgraduate.",
            },
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Additional App Configuration
PAGE_CONFIG = {
    "page_title": "LO Generator",
    "page_icon": "️🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

def build_user_prompt(user_input):
    """
    Dynamically build the user prompt based on conditions and user input.
    """
    user_prompt_parts = []
    
    for prompt_config in PHASES["generate_objectives"]["user_prompt"]:
        if all(user_input.get(key) == value for key, value in prompt_config.get("condition", {}).items()):
            user_prompt_parts.append(prompt_config["prompt"].format(**user_input))

    return "\n".join(user_prompt_parts)

from core_logic.main import main

# Main entry point
if __name__ == "__main__":
    main(config=globals())
