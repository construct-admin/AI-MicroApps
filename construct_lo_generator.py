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
            "request_type": {
                "type": "radio",
                "label": "What would you like to do?",
                "options": [
                    "Provide learning objectives based on the content",
                    "Suggest learning objectives based on the title",
                    "Validate alignment between learning content and objectives"
                ],
            },
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module.",
                "value": "Introduction to Consumer Behavior",
                "showIf": {"request_type": ["Suggest learning objectives based on the title"]}
            },
            "learning_content": {
                "type": "text_area",
                "label": "Enter the learning content:",
                "height": 200,
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Validate alignment between learning content and objectives"]}
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3,
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "real_world_relevance": {
                "type": "checkbox",
                "label": "Prioritize objectives that have real-world relevance.",
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "bloom_taxonomy": {
                "type": "markdown",
                "body": """<h3>Bloom's Taxonomy</h3> Select cognitive goals to focus on:""",
                "unsafe_allow_html": True,
                "showIf": {"request_type": ["Provide learning objectives based on the content", "Suggest learning objectives based on the title"]}
            },
            "goal_apply": {"type": "checkbox", "label": "Apply"},
            "goal_evaluate": {"type": "checkbox", "label": "Evaluate"},
            "goal_analyze": {"type": "checkbox", "label": "Analyze"},
            "goal_create": {"type": "checkbox", "label": "Create"},
        },
        "user_prompt": [
            {
                "condition": {"request_type": "Provide learning objectives based on the content"},
                "prompt": "Based on the content provided, generate {lo_quantity} specific, measurable learning objectives. Ensure alignment with Bloom's taxonomy."
            },
            {
                "condition": {"request_type": "Suggest learning objectives based on the title"},
                "prompt": "Generate {lo_quantity} learning objectives based on the course/module title: {title}. Ensure objectives are specific and aligned with Bloom's taxonomy."
            },
            {
                "condition": {"real_world_relevance": True},
                "prompt": "Prioritize objectives that focus on real-world applications and industry relevance."
            },
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

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
