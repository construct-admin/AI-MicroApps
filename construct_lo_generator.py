import streamlit as st

PUBLISHED = True
APP_URL = "https://lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

APP_TITLE = "Learning Objectives Builder"
APP_INTRO = """This micro-app allows you to generate learning objectives or validate alignment for existing learning objectives. It is meant to explore how generative AI can streamline instructional design processes."""
APP_HOW_IT_WORKS = """
1. Fill in the details of your course/module.
2. Configure the prompt and additional options.
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
                "label": "Enter the course-level learning objective:",
                "height": 200,
                "showIf": {"request_type": ["Provide learning objectives based on the course learning objectives"]}
            },
            "quiz_lo": {
                "type": "text_area",
                "label": "Enter the graded assessment question(s):",
                "height": 200,
                "showIf": {"request_type": ["Provide learning objectives based on the graded assessment question(s) of the module"]}
            },
            "form_lo": {
                "type": "text_area",
                "label": "Enter the formative activity questions:",
                "height": 200,
                "showIf": {"request_type": ["Provide learning objectives based on the formative activity questions"]}
            },
            "lo_quantity": {
                "type": "slider",
                "label": "How many learning objectives would you like to generate?",
                "min_value": 1,
                "max_value": 6,
                "value": 3
            },
            "relevance": {
                "type": "checkbox",
                "label": "Prioritize objectives with real-world relevance."
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
                "body": "<h3>Bloom's Taxonomy</h3> Select cognitive goals to focus on:",
                "unsafe_allow_html": True,
            },
            "goal_apply": {"type": "checkbox", "label": "Apply"},
            "goal_evaluate": {"type": "checkbox", "label": "Evaluate"},
            "goal_analyze": {"type": "checkbox", "label": "Analyze"},
            "goal_create": {"type": "checkbox", "label": "Create"}
        }
    }
}

# Function to handle dynamic prompt generation
def generate_prompt(user_input):
    """Construct the final prompt based on user input."""
    bloom_goals = []
    if user_input.get("goal_apply"):
        bloom_goals.append("Apply")
    if user_input.get("goal_evaluate"):
        bloom_goals.append("Evaluate")
    if user_input.get("goal_analyze"):
        bloom_goals.append("Analyze")
    if user_input.get("goal_create"):
        bloom_goals.append("Create")

    relevance_prompts = []
    if user_input.get("relevance"):
        relevance_prompts.append("Prioritize real-world relevance.")
    if user_input.get("problem_solving"):
        relevance_prompts.append("Focus on problem-solving and critical thinking.")
    if user_input.get("meta_cognitive_reflection"):
        relevance_prompts.append("Focus on meta-cognitive reflections.")
    if user_input.get("ethical_consideration"):
        relevance_prompts.append("Include emotional, moral, and ethical considerations.")

    base_prompt = f"Generate {user_input['lo_quantity']} learning objectives."
    bloom_prompt = f" Focus on these cognitive goals: {', '.join(bloom_goals)}." if bloom_goals else ""
    relevance_prompt = " ".join(relevance_prompts)

    request_type = user_input["request_type"]
    content_prompt = ""
    if request_type == "Suggest learning objectives based on the title":
        content_prompt = f"Title: {user_input['title']}"
    elif request_type == "Provide learning objectives based on the course learning objectives":
        content_prompt = f"Course-level Objectives: {user_input['course_lo']}"
    elif request_type == "Provide learning objectives based on the graded assessment question(s) of the module":
        content_prompt = f"Graded Assessments: {user_input['quiz_lo']}"
    elif request_type == "Provide learning objectives based on the formative activity questions":
        content_prompt = f"Formative Activities: {user_input['form_lo']}"

    return f"{base_prompt} {content_prompt} {bloom_prompt} {relevance_prompt}"

# Main function
def main(config):
    st.set_page_config(page_title=config["APP_TITLE"], page_icon="🔹", layout="centered")
    st.title(config["APP_TITLE"])
    st.write(config["APP_INTRO"])
    st.write(config["APP_HOW_IT_WORKS"])

    # Phase handling
    phase = PHASES["generate_objectives"]
    user_input = {}
    for field_key, field_data in phase["fields"].items():
        if field_data["type"] == "radio":
            user_input[field_key] = st.radio(field_data["label"], field_data["options"])
        elif field_data["type"] == "text_input":
            user_input[field_key] = st.text_input(field_data["label"], "")
        elif field_data["type"] == "text_area":
            user_input[field_key] = st.text_area(field_data["label"], "", height=field_data.get("height", 200))
        elif field_data["type"] == "slider":
            user_input[field_key] = st.slider(
                field_data["label"],
                field_data["min_value"],
                field_data["max_value"],
                field_data["value"]
            )
        elif field_data["type"] == "checkbox":
            user_input[field_key] = st.checkbox(field_data["label"])
        elif field_data["type"] == "markdown":
            st.markdown(field_data["body"], unsafe_allow_html=field_data.get("unsafe_allow_html", False))

    if st.button("Generate Prompt"):
        prompt = generate_prompt(user_input)
        st.text_area("Generated Prompt", prompt, height=200)

if __name__ == "__main__":
    main(config=globals())
