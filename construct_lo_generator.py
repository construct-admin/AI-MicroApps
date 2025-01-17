PUBLISHED = True
APP_URL = "https://construct-lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Generator"
APP_INTRO = """This micro-app allows you to generate learning objectives or validate alignment for existing learning objectives. It streamlines instructional design by integrating AI to enhance efficiency and personalization."""
APP_HOW_IT_WORKS = """
1. Fill in the details of your course/module.
2. Configure cognitive goals and relevance preferences.
3. Generate specific, measurable, and aligned learning objectives.
"""

SYSTEM_PROMPT = """You are EduDesignGPT, an expert instructional designer specialized in creating clear, specific, and measurable module-level learning objectives for online courses."""

def add_preferences_to_prompt(user_input):
    prompt = ""
    if user_input.get("real_world_relevance"):
        prompt += "Try to provide learning objectives that are relevant to real-world practices and industry trends.\n"
    if user_input.get("problem_solving"):
        prompt += "Try to provide objectives that focus on problem-solving and critical thinking.\n"
    if user_input.get("meta_cognitive_reflection"):
        prompt += "Try to provide objectives that focus on meta-cognitive reflections.\n"
    if user_input.get("ethical_consideration"):
        prompt += "Try to provide objectives that include emotional, moral, and ethical considerations.\n"
    return prompt

def add_bloom_goals_to_prompt(user_input):
    bloom_goals = []
    if user_input.get("goal_apply"):
        bloom_goals.append("Apply")
    if user_input.get("goal_evaluate"):
        bloom_goals.append("Evaluate")
    if user_input.get("goal_analyze"):
        bloom_goals.append("Analyze")
    if user_input.get("goal_create"):
        bloom_goals.append("Create")
    return f"Focus specifically on these cognitive goals: {', '.join(bloom_goals)}.\n" if bloom_goals else ""

def add_academic_stage_to_prompt(user_input):
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
    return f"Target the following academic stage(s): {', '.join(stages)}.\n" if stages else ""

def prompt_conditionals(prompt, user_input, phase_name="generate_objectives"):
    preferences = add_preferences_to_prompt(user_input)
    bloom_goals = add_bloom_goals_to_prompt(user_input)
    academic_stage = add_academic_stage_to_prompt(user_input)

    if user_input["request_type"] == "Suggest learning objectives based on the title":
        prompt = (
            f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input['title']}.\n"
            f"{preferences}{bloom_goals}{academic_stage}"
        )
    elif user_input["request_type"] == "Provide learning objectives based on the course learning objectives":
        prompt = (
            f"Please write {user_input['lo_quantity']} module learning objectives based on the provided course-level learning objectives: {user_input['course_lo']}.\n"
            f"{preferences}{bloom_goals}{academic_stage}"
        )
    elif user_input["request_type"] == "Provide learning objectives based on the graded assessment question(s) of the module":
        prompt = (
            f"Please write {user_input['lo_quantity']} module learning objectives based on the graded quiz questions: {user_input['quiz_lo']}.\n"
            f"{preferences}{bloom_goals}{academic_stage}"
        )
    elif user_input["request_type"] == "Provide learning objectives based on the formative activity questions":
        prompt = (
            f"Please write {user_input['lo_quantity']} module learning objectives based on the formative activity questions: {user_input['form_lo']}.\n"
            f"{preferences}{bloom_goals}{academic_stage}"
        )
    else:
        prompt = "Invalid request type."
    return prompt

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

PAGE_CONFIG = {
    "page_title": "LO Generator",
    "page_icon": "🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
