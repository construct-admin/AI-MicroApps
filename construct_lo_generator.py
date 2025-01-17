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
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}

def prompt_conditionals(prompt, user_input, phase_name=None):
    if user_input["request_type"] == "Suggest learning objectives based on the title":
        prompt = (
             "Please suggest {lo_quantity} module learning objectives for the provided title: {title}.\n"
             + "Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.")
        if user_input["real_world_relevance"]:
             prompt += (
             "Try to provide learning objectives that are relevant to real-world practices and industry trends. \n"
             )
        if user_input["problem_solving"]:
             prompt += (
             "Try to provide objectives that focus on problem-solving and critical thinking. \n"
             )
        if user_input["meta_cognitive_reflection"]:
             prompt += (
             "Try to provide objectives that focus on meta-cognitive reflections. \n"
             )
        if user_input["ethical_consideration"]:
             prompt += (
             "Try to provide objectives that include emotional, moral, and ethical considerations. \n"
             )
        if any([user_input["goal_apply"], user_input["goal_evaluate"], user_input["goal_analyze"], user_input["goal_create"]]):
            prompt += "Focus specifically on these cognitive goals: "  + "\n"
            if user_input["goal_apply"]:
                prompt+= "Apply \n"
            if user_input["goal_evaluate"]:
                prompt+= "Evaluate \n"
            if user_input["goal_understand"]:
                prompt+= "Understand \n"
            if user_input["goal_analyze"]:
                prompt+= "Analyze \n"
            if user_input["goal_create"]:
                prompt+= "Create \n"
            prompt += ". \n"
        if any([user_input["lower_primary"], user_input["middle_primary"], user_input["upper_primary"], user_input["lower_secondary"], user_input["upper_secondary"], user_input["undergraduate"], user_input["postgraduate"]]):
            prompt += "Target the following academic stage(s): " + "\n"
            if user_input["lower_primary"]:
                prompt += "Lower Primary \n"
            if user_input["middle_primary"]:
                prompt += "Middle Primary \n"
            if user_input["upper_primary"]:
                prompt += "Upper Primary \n"
            if user_input["lower_secondary"]:
                prompt += "Lower Secondary \n"
            if user_input["upper_secondary"]:
                prompt += "Upper Secondary \n"
            if user_input["undergraduate"]:
                prompt += "Undergraduate \n"
            if user_input["postgraduate"]:
                prompt += "Postgraduate \n"
            prompt += ". \n"
    else:
        if user_input["request_type"] == "Provide learning objectives based on the course learning objectives":
            prompt = (
             "Please write {lo_quantity} module learning objectives based on the provided course level learning objectives. \n {course_lo}"
             + "Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.")
        if user_input["real_world_relevance"]:
             prompt += (
             "Try to provide learning objectives that are relevant to real-world practices and industry trends. \n"
             )
        if user_input["problem_solving"]:
             prompt += (
             "Try to provide objectives that focus on problem-solving and critical thinking. \n"
             )
        if user_input["meta_cognitive_reflection"]:
             prompt += (
             "Try to provide objectives that focus on meta-cognitive reflections. \n"
             )
        if user_input["ethical_consideration"]:
             prompt += (
             "Try to provide objectives that include emotional, moral, and ethical considerations. \n"
             )
        if any([user_input["goal_apply"], user_input["goal_evaluate"], user_input["goal_analyze"], user_input["goal_create"]]):
            prompt += "Focus specifically on these cognitive goals: "  + "\n"
            if user_input["goal_apply"]:
                prompt+= "Apply \n"
            if user_input["goal_evaluate"]:
                prompt+= "Evaluate \n"
            if user_input["goal_understand"]:
                prompt+= "Understand \n"
            if user_input["goal_analyze"]:
                prompt+= "Analyze \n"
            if user_input["goal_create"]:
                prompt+= "Create \n"
            prompt += ". \n"
        if any([user_input["lower_primary"], user_input["middle_primary"], user_input["upper_primary"], user_input["lower_secondary"], user_input["upper_secondary"], user_input["undergraduate"], user_input["postgraduate"]]):
            prompt += "Target the following academic stage(s): " + "\n"
            if user_input["lower_primary"]:
                prompt += "Lower Primary \n"
            if user_input["middle_primary"]:
                prompt += "Middle Primary \n"
            if user_input["upper_primary"]:
                prompt += "Upper Primary \n"
            if user_input["lower_secondary"]:
                prompt += "Lower Secondary \n"
            if user_input["upper_secondary"]:
                prompt += "Upper Secondary \n"
            if user_input["undergraduate"]:
                prompt += "Undergraduate \n"
            if user_input["postgraduate"]:
                prompt += "Postgraduate \n"
            prompt += ". \n"
        else:
            if user_input["request_type"] == "Provide learning objectives based on the graded assessment question(s) of the module":
                prompt = (
                "Please write {lo_quantity} module learning objectives based on the provided graded quiz questions. \n {quiz_lo}"
             + "Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.")
            if user_input["real_world_relevance"]:
                prompt += (
                "Try to provide learning objectives that are relevant to real-world practices and industry trends. \n"
                )
            if user_input["problem_solving"]:
                prompt += (
                "Try to provide objectives that focus on problem-solving and critical thinking. \n"
                )
            if user_input["meta_cognitive_reflection"]:
                prompt += (
                "Try to provide objectives that focus on meta-cognitive reflections. \n"
                )
            if user_input["ethical_consideration"]:
                prompt += (
                "Try to provide objectives that include emotional, moral, and ethical considerations. \n"
                )
            if any([user_input["goal_apply"], user_input["goal_evaluate"], user_input["goal_analyze"], user_input["goal_create"]]):
                prompt += "Focus specifically on these cognitive goals: "  + "\n"
                if user_input["goal_apply"]:
                    prompt+= "Apply \n"
                if user_input["goal_evaluate"]:
                    prompt+= "Evaluate \n"
                if user_input["goal_understand"]:
                    prompt+= "Understand \n"
                if user_input["goal_analyze"]:
                    prompt+= "Analyze \n"
                if user_input["goal_create"]:
                    prompt+= "Create \n"
                prompt += ". \n"
            if any([user_input["lower_primary"], user_input["middle_primary"], user_input["upper_primary"], user_input["lower_secondary"], user_input["upper_secondary"], user_input["undergraduate"], user_input["postgraduate"]]):
                prompt += "Target the following academic stage(s): " + "\n"
                if user_input["lower_primary"]:
                    prompt += "Lower Primary \n"
                if user_input["middle_primary"]:
                    prompt += "Middle Primary \n"
                if user_input["upper_primary"]:
                    prompt += "Upper Primary \n"
                if user_input["lower_secondary"]:
                    prompt += "Lower Secondary \n"
                if user_input["upper_secondary"]:
                    prompt += "Upper Secondary \n"
                if user_input["undergraduate"]:
                    prompt += "Undergraduate \n"
                if user_input["postgraduate"]:
                    prompt += "Postgraduate \n"
                prompt += ". \n"
            else:
                if user_input["request_type"] == "Provide learning objectives based on the graded assessment question(s) of the module":
                    prompt = (
                    "Please write {lo_quantity} module learning objectives based on the formative activity questions. \n {form_lo}"
                + "Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.")
                if user_input["real_world_relevance"]:
                    prompt += (
                    "Try to provide learning objectives that are relevant to real-world practices and industry trends. \n"
                    )
                if user_input["problem_solving"]:
                    prompt += (
                    "Try to provide objectives that focus on problem-solving and critical thinking. \n"
                    )
                if user_input["meta_cognitive_reflection"]:
                    prompt += (
                    "Try to provide objectives that focus on meta-cognitive reflections. \n"
                    )
                if user_input["ethical_consideration"]:
                    prompt += (
                    "Try to provide objectives that include emotional, moral, and ethical considerations. \n"
                    )
                if any([user_input["goal_apply"], user_input["goal_evaluate"], user_input["goal_analyze"], user_input["goal_create"]]):
                    prompt += "Focus specifically on these cognitive goals: "  + "\n"
                if user_input["goal_apply"]:
                    prompt+= "Apply \n"
                if user_input["goal_evaluate"]:
                    prompt+= "Evaluate \n"
                if user_input["goal_understand"]:
                    prompt+= "Understand \n"
                if user_input["goal_analyze"]:
                    prompt+= "Analyze \n"
                if user_input["goal_create"]:
                    prompt+= "Create \n"
                prompt += ". \n"
                if any([user_input["lower_primary"], user_input["middle_primary"], user_input["upper_primary"], user_input["lower_secondary"], user_input["upper_secondary"], user_input["undergraduate"], user_input["postgraduate"]]):
                    prompt += "Target the following academic stage(s): " + "\n"
                if user_input["lower_primary"]:
                    prompt += "Lower Primary \n"
                if user_input["middle_primary"]:
                    prompt += "Middle Primary \n"
                if user_input["upper_primary"]:
                    prompt += "Upper Primary \n"
                if user_input["lower_secondary"]:
                    prompt += "Lower Secondary \n"
                if user_input["upper_secondary"]:
                    prompt += "Upper Secondary \n"
                if user_input["undergraduate"]:
                    prompt += "Undergraduate \n"
                if user_input["postgraduate"]:
                    prompt += "Postgraduate \n"
                prompt += ". \n"
    return prompt



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
