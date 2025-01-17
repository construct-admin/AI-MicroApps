PUBLISHED = True
APP_URL = "https://construct-lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Generator"
APP_INTRO = """This application is based on constructive alignment principles. It allows you to generate learning objectives that align with your course-level learning objectives, assessments, and activities. Furthermore, it can be used to enhance existing learning objectives and validate objective alignment."""

APP_HOW_IT_WORKS = """
1. Provide details about your course/module.
2. Select cognitive goals, relevance preferences, and academic stage.
3. Generate specific, measurable, and aligned learning objectives.
"""

SYSTEM_PROMPT = """You are EduDesignGPT, an expert instructional designer specialized in creating clear, specific, and measurable module-level learning objectives for online courses. Your purpose is to assist course creators in developing learning objectives that align with best practices for online education."""

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
                "label": "Enter the title of your module.",
                "showIf": {"request_type": ["Suggest learning objectives based on the title"]}
            },
            "course_lo": {
                "type": "text_area",
                "label": "Enter the course learning objective: ",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the course learning objectives"]}
            },
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s) of the module.",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the graded assessment question(s) of the module"]}
            },
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity question(s) of the module",
                "height": 300,
                "showIf": {"request_type": ["Provide learning objectives based on the formative activity questions"]}
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3
            },
            "real_world_relevance": {
                "type": "checkbox",
                "label": "Prioritize objectives that have real-world relevance."
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
                "unsafe_allow_html": True,
            },
            "goal_apply": {"type": "checkbox", "label": "Apply"},
            "goal_evaluate": {"type": "checkbox", "label": "Evaluate"},
            "goal_analyze": {"type": "checkbox", "label": "Analyze"},
            "goal_create": {"type": "checkbox", "label": "Create"},
            "academic_stage": {
                "type": "markdown",
                "body": """<h3>Academic Stage:</h3>
                Select the category that best reflects the academic stage of the students:""",
                "unsafe_allow_html": True,
            },
            "lower_primary": {"type": "checkbox", "label": "Lower Primary"},
            "middle_primary": {"type": "checkbox", "label": "Middle Primary"},
            "upper_primary": {"type": "checkbox", "label": "Upper Primary"},
            "lower_secondary": {"type": "checkbox", "label": "Lower Secondary"},
            "upper_secondary": {"type": "checkbox", "label": "Upper Secondary"},
            "undergraduate": {"type": "checkbox", "label": "Undergraduate"},
            "postgraduate": {"type": "checkbox", "label": "Postgraduate"},
        },
        "user_prompt": [
            {
                "condition": {"request_type": "Provide learning objectives based on the content"},
                "prompt": """Please write {lo_quantity} module learning objectives based on the provided content. 
                {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"""
            },
            {
                "condition": {"request_type": "Suggest learning objectives based on the title"},
                "prompt": """Please suggest {lo_quantity} module learning objectives for the provided title: {title}. 
                {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"""
            },
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

# Helper functions for dynamic prompt construction
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
