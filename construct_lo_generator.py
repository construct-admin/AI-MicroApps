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
                "type": "radio",
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
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Function to handle Bloom's Taxonomy prompts
def get_bloom_prompt(user_input):
    bloom_goals = []
    if user_input.get("goal_apply"):
        bloom_goals.append("Apply")
    if user_input.get("goal_evaluate"):
        bloom_goals.append("Evaluate")
    if user_input.get("goal_analyze"):
        bloom_goals.append("Analyze")
    if user_input.get("goal_create"):
        bloom_goals.append("Create")
    if bloom_goals:
        return f"Start each learning objective with a verb from Bloom's taxonomy. **Avoid** verbs like understand, learn or know\. {', '.join(bloom_goals)}."
    return ""

# Function to handle relevance preferences
def get_relevance_prompt(user_input):
    relevance_prompts = []
    if user_input.get("real_world_relevance"):
        relevance_prompts.append("Try to provide learning objectives that are relevant to real-world practices and industry trends.")
    if user_input.get("problem_solving"):
        relevance_prompts.append("Try to provide objectives that focus on problem-solving and critical thinking.")
    if user_input.get("meta_cognitive_reflection"):
        relevance_prompts.append("Try to provide objectives that focus on meta-cognitive reflections.")
    if user_input.get("ethical_consideration"):
        relevance_prompts.append("Try to provide objectives that include emotional, moral, and ethical considerations.")
    return " ".join(relevance_prompts)

# Function to handle academic stage prompts
def get_academic_stage_prompt(user_input):
    stages = []
    if user_input.get("lower_primary"):
        stages.append("Lower Primary")
    if user_input.get("middle_primary"):
        stages.append("Middle Primary")
    if user_input.get("upper_primary"):
        stages.append("Upper Primary")
    if user_input.get("lower_secondary"):
        stages.append("Lower Secondary")
    if user_input.get("upper_secondary"):
        stages.append("Upper Secondary")
    if user_input.get("undergraduate"):
        stages.append("Undergraduate")
    if user_input.get("postgraduate"):
        stages.append("Postgraduate")
    if stages:
        return f"Target the following academic stage(s): {', '.join(stages)}."
    return ""

# Function to generate the final prompt
def generate_final_prompt(user_input):
    bloom_prompt = get_bloom_prompt(user_input)
    relevance_prompt = get_relevance_prompt(user_input)
    academic_stage_prompt = get_academic_stage_prompt(user_input)

    if user_input["request_type"] == "Suggest learning objectives based on the title":
        return f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input['title']}. {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"
    elif user_input["request_type"] == "Provide learning objectives based on the course learning objectives":
        return f"Please write {user_input['lo_quantity']} module learning objectives based on the provided course-level learning objectives: {user_input['course_lo']}. {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"
    elif user_input["request_type"] == "Provide learning objectives based on the graded assessment question(s) of the module":
        return f"Please write {user_input['lo_quantity']} module learning objectives based on the graded quiz questions: {user_input['quiz_lo']}. {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"
    elif user_input["request_type"] == "Provide learning objectives based on the formative activity questions":
        return f"Please write {user_input['lo_quantity']} module learning objectives based on the formative activity questions: {user_input['form_lo']}. {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"
    return "Invalid request type."

# Additional App Configuration
PAGE_CONFIG = {
    "page_title": "LO Generator",
    "page_icon": "️🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

from core_logic.main import main

# Main entry point
if __name__ == "__main__":
    main(config=globals())
