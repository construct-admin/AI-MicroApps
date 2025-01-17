PUBLISHED = True
APP_URL = "https://lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Builder"
APP_INTRO = """This micro-app allows you to generate learning objectives or validate alignment for existing learning objectives. It is meant as an experiment to explore how adoption, efficiency, and shareability of generative AI is affected when you wrap lightweight, hyper-personalized wrappers around it. Wrappers like this can take a few hours to build, which fast enough to justify building different micro-apps for different use cases. They also ideally codify good practices (in this case, instructional design practices) into AI prompting. 
"""

APP_HOW_IT_WORKS = """
 1. Fill in the details of the assessment.
2. Choose the language model.
3. Configure the prompt and additional options.
4. Generate Learning Objectives.
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

def build_prompt(user_input):
    """Builds a dynamic prompt based on user input."""
    # Start with the base prompt
    prompt = ""

    # Add title or request-specific details
    request_type = user_input.get("request_type", "Invalid request type")
    lo_quantity = user_input.get("lo_quantity", 1)

    if request_type == "Suggest learning objectives based on the title":
        title = user_input.get("title", "Untitled Module")
        prompt += f"Please suggest {lo_quantity} module learning objectives for the provided title: {title}.\n"
    elif request_type == "Provide learning objectives based on the course learning objectives":
        course_lo = user_input.get("course_lo", "")
        prompt += f"Please write {lo_quantity} module learning objectives based on the provided course-level learning objectives: {course_lo}.\n"
    elif request_type == "Provide learning objectives based on the graded assessment question(s) of the module":
        quiz_lo = user_input.get("quiz_lo", "")
        prompt += f"Please write {lo_quantity} module learning objectives based on the graded quiz questions: {quiz_lo}.\n"
    elif request_type == "Provide learning objectives based on the formative activity questions":
        form_lo = user_input.get("form_lo", "")
        prompt += f"Please write {lo_quantity} module learning objectives based on the formative activity questions: {form_lo}.\n"
    else:
        prompt += "Invalid request type.\n"

    # Append preferences
    if user_input.get("real_world_relevance"):
        prompt += "Focus on real-world practices and industry trends.\n"
    if user_input.get("problem_solving"):
        prompt += "Focus on problem-solving and critical thinking.\n"
    if user_input.get("meta_cognitive_reflection"):
        prompt += "Focus on meta-cognitive reflections.\n"
    if user_input.get("ethical_consideration"):
        prompt += "Include emotional, moral, and ethical considerations.\n"

    # Append Bloom's taxonomy goals
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

    # Append academic stage
    academic_stages = []
    if user_input.get("lower_primary"):
        academic_stages.append("Lower Primary")
    if user_input.get("middle_primary"):
        academic_stages.append("Middle Primary")
    if user_input.get("upper_primary"):
        academic_stages.append("Upper Primary")
    if user_input.get("lower_secondary"):
        academic_stages.append("Lower Secondary")
    if user_input.get("upper_secondary"):
        academic_stages.append("Upper Secondary")
    if user_input.get("undergraduate"):
        academic_stages.append("Undergraduate")
    if user_input.get("postgraduate"):
        academic_stages.append("Postgraduate")
    if academic_stages:
        prompt += f"Target the following academic stage(s): {', '.join(academic_stages)}.\n"

    # Assign the final prompt to user_prompt
    user_prompt = prompt
    return user_prompt
    
PREFERRED_LLM = "gpt-4o-mini"
LLM_CONFIG_OVERRIDE = {}

SCORING_DEBUG_MODE = True
DISPLAY_COST = True

PAGE_CONFIG = {
    "page_title": "LO Generator",
    "page_icon": "️🔹",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())