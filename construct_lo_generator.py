PUBLISHED = True
APP_URL = "https://construct-lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Generator"
APP_INTRO = """This application is based on constructive alignment principles. It allows you to generate learning objectives that are aligned with your course-level learning objectives, assessments, and activities. Furthermore, it can be used to enhance existing learning objectives and validate objective alignment."""
APP_HOW_IT_WORKS = """
1. Provide details about your course/module.
2. Select cognitive goals and relevance preferences.
3. Generate specific, measurable, and aligned learning objectives.
"""

SYSTEM_PROMPT = "You are EduDesignGPT, an expert instructional designer specialized in creating clear, specific, and measurable modulde-level learning objectives for online courses. Your purpose is to assist course creators in developing learning objectives that align with best practices for online education."

PHASES = {
    "generate_objectives": {
        "name": "Generate Learning Objectives",
        "fields": {
            # User selects the type of request they want to make
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
            # Input for the module title (optional, based on request type)
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module.",
                "showIf": {"request_type": ["Suggest learning objectives based on the title"]}
            },
            # Input for course-level learning objectives
            "course_lo": {
                "type": "text_area",
                "label": "Enter the course learning objective: ",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the course learning objectives"]}
            },
            # Input for graded assessment questions
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s) of the module.",
                "height": 500,
                "showIf": {"request_type": ["Provide learning objectives based on the graded assessment question(s) of the module"]}
            },
            # Input for formative activity questions
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity question(s) of the module",
                "height": 500,
                "showIf": {"request_type": ["Provide learning objectives based on the formative activity questions"]}
            },
            # Slider to determine how many learning objectives to generate
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
            # Section for Bloom's Taxonomy
            "bloom_taxonomy": {
                "type": "markdown",
                "body": """<h3>Bloom's Taxonomy</h3> Select cognitive goals to focus on:""",
                "unsafe_allow_html": True,
            },
            # Bloom's Taxonomy goal checkboxes
            "goal_apply": {"type": "checkbox", "label": "Apply"},
            "goal_evaluate": {"type": "checkbox", "label": "Evaluate"},
            "goal_analyze": {"type": "checkbox", "label": "Analyze"},
            "goal_create": {"type": "checkbox", "label": "Create"},
            # Academic Stage section
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
        # The dynamically generated prompt
        "user_prompt": [
            {
                "condition": {"request_type": "Provide learning objectives based on the course learning objectives"},
                "prompt": lambda user_input: f"Please write {user_input['lo_quantity']} module learning objectives based on the provided course-level learning objectives: {user_input['course_lo']}.\n" 
                                              f"{get_bloom_prompt(user_input)} {get_relevance_prompt(user_input)} {get_academic_stage_prompt(user_input)}"
            },
            {
                "condition": {"request_type": "Suggest learning objectives based on the title"},
                "prompt": lambda user_input: f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input['title']}.\n" 
                                              f"{get_bloom_prompt(user_input)} {get_relevance_prompt(user_input)} {get_academic_stage_prompt(user_input)}"
            },
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Function to get Bloom's Taxonomy goals
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
        return f"Focus on the following cognitive goals: {', '.join(bloom_goals)}."
    return ""

# Function to get relevance prompts
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

# Function to get Academic Stage prompts
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


PREFERRED_LLM = "gpt-4o-mini"
LLM_CONFIG_OVERRIDE = {"temperature": 0.3}

PAGE_CONFIG = {
    "page_title": "Learning Objectives Generator",
    "page_icon": "🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
