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
        "user_prompt": "{user_prompt}",
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

def append_preferences(user_prompt, user_input):
    """Append preferences to the user_prompt based on user input."""
    preferences = []
    if user_input.get("real_world_relevance"):
        preferences.append("real-world practices and industry trends")
    if user_input.get("problem_solving"):
        preferences.append("problem-solving and critical thinking")
    if user_input.get("meta_cognitive_reflection"):
        preferences.append("meta-cognitive reflections")
    if user_input.get("ethical_consideration"):
        preferences.append("emotional, moral, and ethical considerations")

    if preferences:
        user_prompt += f" Focus on the following preferences: {', '.join(preferences)}.\n"
    return user_prompt

def append_bloom_taxonomy(user_prompt, user_input):
    """Append Bloom's taxonomy goals to the user_prompt."""
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
        user_prompt += f" Focus specifically on these cognitive goals: {', '.join(bloom_goals)}.\n"
    return user_prompt

def append_academic_stage(user_prompt, user_input):
    """Append academic stage information to the user_prompt."""
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
        user_prompt += f" Target the following academic stage(s): {', '.join(stages)}.\n"
    return user_prompt

def prompt_conditionals(user_input, phase_name=None):
    """Generate a complete user_prompt dynamically based on user input."""
    request_type = user_input.get("request_type", "Invalid request type")
    lo_quantity = user_input.get("lo_quantity", 1)
    title = user_input.get("title", "Untitled Module")  # Handle missing title gracefully

    # Initialize user_prompt
    user_prompt = ""

    # Construct prompt based on request type
    if request_type == "Suggest learning objectives based on the title":
        user_prompt = f"Please suggest {lo_quantity} module learning objectives for the provided title: {title}.\n"
    elif request_type == "Provide learning objectives based on the course learning objectives":
        course_lo = user_input.get("course_lo", "No course objectives provided.")
        user_prompt = f"Please write {lo_quantity} module learning objectives based on the provided course-level learning objectives: {course_lo}.\n"
    elif request_type == "Provide learning objectives based on the graded assessment question(s) of the module":
        quiz_lo = user_input.get("quiz_lo", "No quiz questions provided.")
        user_prompt = f"Please write {lo_quantity} module learning objectives based on the graded quiz questions: {quiz_lo}.\n"
    elif request_type == "Provide learning objectives based on the formative activity questions":
        form_lo = user_input.get("form_lo", "No formative activity questions provided.")
        user_prompt = f"Please write {lo_quantity} module learning objectives based on the formative activity questions: {form_lo}.\n"
    else:
        user_prompt = "Invalid request type. Please select a valid option."

    # Append additional preferences
    user_prompt = append_preferences(user_prompt, user_input)

    # Append Bloom's Taxonomy goals
    user_prompt = append_bloom_taxonomy(user_prompt, user_input)

    # Append academic stage details
    user_prompt = append_academic_stage(user_prompt, user_input)

    # Log the final prompt for debugging
    print("Generated user_prompt:", user_prompt)

    # Return the constructed prompt
    return user_prompt

# Additional App Configuration
PAGE_CONFIG = {
    "page_title": "Construct LO Generator",
    "page_icon": "️🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

from core_logic.main import main

# Main entry point
if __name__ == "__main__":
    main(config=globals())
