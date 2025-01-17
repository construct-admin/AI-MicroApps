# Define whether the app is published and some app-level metadata
PUBLISHED = True
APP_URL = "https://construct-lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

# App title and introduction displayed to users
APP_TITLE = "Learning Objectives Generator"
APP_INTRO = """This application is based on constructive alignment principles. It allows you to generate learning objectives that are aligned with your course-level learning objectives, assessments, and activities. Furthermore, it can be used to enhance existing learning objectives and validate objective alignment."""

# Step-by-step instructions for users
APP_HOW_IT_WORKS = """
1. Provide details about your course/module.
2. Select cognitive goals and relevance preferences.
3. Generate specific, measurable, and aligned learning objectives.
"""

# The system prompt that defines the AI's behavior
SYSTEM_PROMPT = "You are EduDesignGPT, an expert instructional designer specialized in creating clear, specific, and measurable module-level learning objectives for online courses. Your purpose is to assist course creators in developing learning objectives that align with best practices for online education."

# Define all the phases and fields for user input
PHASES = {
    "generate_objectives": {
        "name": "Generate Learning Objectives",
        "fields": {
            # Radio buttons for selecting the type of request
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
            # Text input for the module title
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module.",
                "showIf": {"request_type": ["Suggest learning objectives based on the title"]}
            },
            # Text area for course-level learning objectives
            "course_lo": {
                "type": "text_area",
                "label": "Enter the course learning objective: ",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the course learning objectives"]}
            },
            # Text area for graded assessment questions
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s) of the module.",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the graded assessment question(s) of the module"]}
            },
            # Text area for formative activity questions
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity question(s) of the module",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the formative activity questions"]}
            },
            # Slider for selecting how many objectives to generate
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3
            },
            # Checkbox for real-world relevance
            "real_world_relevance": {
                "type": "checkbox",
                "label": "Try to provide learning objectives that are relevant to real-world practices and industry trends."
            },
            # Additional checkboxes for critical thinking, reflection, and ethics
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
            # Section for Bloom's Taxonomy goals
            "bloom_taxonomy": {
                "type": "markdown",
                "body": """<h3>Bloom's Taxonomy</h3> Select cognitive goals to focus on:""",
                "unsafe_allow_html": True,
            },
            # Bloom's Taxonomy checkboxes
            "goal_apply": {"type": "checkbox", "label": "Apply"},
            "goal_evaluate": {"type": "checkbox", "label": "Evaluate"},
            "goal_analyze": {"type": "checkbox", "label": "Analyze"},
            "goal_create": {"type": "checkbox", "label": "Create"},
            # Academic Stage Section
            "academic_stage": {
                "type": "markdown",
                "body": """<h3>Academic Stage:</h3>
                Select the category that best reflects the academic stage of the students:""",
                "unsafe_allow_html": True,
            },
            # Academic Stage checkboxes
            "lower_primary": {"type": "checkbox", "label": "Lower Primary"},
            "middle_primary": {"type": "checkbox", "label": "Middle Primary"},
            "upper_primary": {"type": "checkbox", "label": "Upper Primary"},
            "lower_secondary": {"type": "checkbox", "label": "Lower Secondary"},
            "upper_secondary": {"type": "checkbox", "label": "Upper Secondary"},
            "undergraduate": {"type": "checkbox", "label": "Undergraduate"},
            "postgraduate": {"type": "checkbox", "label": "Postgraduate"},
        },
        # The dynamically generated prompt using the `prompt_conditionals` function
        "user_prompt": [
            {
                "condition": {},
                "prompt": lambda user_input: prompt_conditionals(user_input)
            }
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Function to build the prompt dynamically based on user input
def prompt_conditionals(user_input):
    """
    Dynamically build the AI prompt based on user input.
    """
    prompt = ""

    # Add the main request type prompt
    if user_input["request_type"] == "Provide learning objectives based on the course learning objectives":
        prompt = f"Please write {user_input['lo_quantity']} module learning objectives based on the provided course-level learning objectives: {user_input.get('course_lo', '')}.\n"
    elif user_input["request_type"] == "Suggest learning objectives based on the title":
        prompt = f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input.get('title', '')}.\n"
    elif user_input["request_type"] == "Provide learning objectives based on the graded assessment question(s) of the module":
        prompt = f"Please suggest {user_input['lo_quantity']} module learning objectives based on the graded quiz questions: {user_input.get('quiz_lo', '')}.\n"
    elif user_input["request_type"] == "Provide learning objectives based on the formative activity questions":
        prompt = f"Please suggest {user_input['lo_quantity']} module learning objectives based on the formative activity questions: {user_input.get('form_lo', '')}.\n"

    # Add Bloom's Taxonomy goals
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
        prompt += f"Focus on the following cognitive goals: {', '.join(bloom_goals)}.\n"

    # Add relevance prompts
    if user_input.get("real_world_relevance"):
        prompt += "Try to provide learning objectives that are relevant to real-world practices and industry trends.\n"
    if user_input.get("problem_solving"):
        prompt += "Try to provide objectives that focus on problem-solving and critical thinking.\n"
    if user_input.get("meta_cognitive_reflection"):
        prompt += "Try to provide objectives that focus on meta-cognitive reflections.\n"
    if user_input.get("ethical_consideration"):
        prompt += "Try to provide objectives that include emotional, moral, and ethical considerations.\n"

    # Add academic stage prompts
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
        prompt += f"Target the following academic stage(s): {', '.join(stages)}.\n"

    return prompt

# App configuration settings
PREFERRED_LLM = "gpt-4o-mini"
LLM_CONFIG_OVERRIDE = {"temperature": 0.3}

PAGE_CONFIG = {
    "page_title": "Learning Objectives Generator",
    "page_icon": "🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

# Main entry point for the app
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
