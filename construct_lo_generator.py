import streamlit as st

# Set up the Streamlit page configuration at the very beginning
st.set_page_config(
    page_title="Learning Objectives Generator",
    page_icon="🔹",
    layout="centered",
    initial_sidebar_state="expanded"
)

# App constants and introductory text
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

# Functions to generate parts of the dynamic prompt

def get_bloom_prompt(user_input):
    """Generate Bloom's Taxonomy goals based on user selection."""
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
    """Generate relevance-related preferences based on user selection."""
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
    """Generate academic stage preferences based on user selection."""
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

def generate_final_prompt(user_input):
    """Combine all components into the final prompt."""
    bloom_prompt = get_bloom_prompt(user_input)
    relevance_prompt = get_relevance_prompt(user_input)
    academic_stage_prompt = get_academic_stage_prompt(user_input)

    if user_input["request_type"] == "Suggest learning objectives based on the title":
        return f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input['title']}. {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"
    elif user_input["request_type"] == "Provide learning objectives based on the course learning objectives":
        return f"Please write {user_input['lo_quantity']} module learning objectives based on the provided course-level learning objectives: {user_input['course_lo']}. {bloom_prompt} {relevance_prompt} {academic_stage_prompt}"
    return "Invalid request type."

# Streamlit User Interface
st.title(APP_TITLE)
st.write(APP_INTRO)
st.write(APP_HOW_IT_WORKS)

# Gather user inputs
request_type = st.radio("What would you like to do?", [
    "Suggest learning objectives based on the title",
    "Provide learning objectives based on the course learning objectives"
])

# Input fields for various request types
title = st.text_input("Enter the title of your module:", "") if request_type == "Suggest learning objectives based on the title" else ""
course_lo = st.text_area("Enter the course learning objective:", "", height=300) if request_type == "Provide learning objectives based on the course learning objectives" else ""
lo_quantity = st.slider("How many learning objectives would you like to generate?", 1, 6, 3)

# Relevance preferences
real_world_relevance = st.checkbox("Prioritize objectives that have real-world relevance.")
problem_solving = st.checkbox("Focus on problem-solving and critical thinking.")
meta_cognitive_reflection = st.checkbox("Focus on meta-cognitive reflections.")
ethical_consideration = st.checkbox("Include emotional, moral, and ethical considerations.")

# Bloom's Taxonomy goals
st.markdown("<h3>Bloom's Taxonomy</h3>", unsafe_allow_html=True)
goal_apply = st.checkbox("Apply")
goal_evaluate = st.checkbox("Evaluate")
goal_analyze = st.checkbox("Analyze")
goal_create = st.checkbox("Create")

# Academic Stage
st.markdown("<h3>Academic Stage:</h3>", unsafe_allow_html=True)
lower_primary = st.checkbox("Lower Primary")
middle_primary = st.checkbox("Middle Primary")
upper_primary = st.checkbox("Upper Primary")
lower_secondary = st.checkbox("Lower Secondary")
upper_secondary = st.checkbox("Upper Secondary")
undergraduate = st.checkbox("Undergraduate")
postgraduate = st.checkbox("Postgraduate")

# Compile user inputs into a dictionary
user_input = {
    "request_type": request_type,
    "title": title,
    "course_lo": course_lo,
    "lo_quantity": lo_quantity,
    "real_world_relevance": real_world_relevance,
    "problem_solving": problem_solving,
    "meta_cognitive_reflection": meta_cognitive_reflection,
    "ethical_consideration": ethical_consideration,
    "goal_apply": goal_apply,
    "goal_evaluate": goal_evaluate,
    "goal_analyze": goal_analyze,
    "goal_create": goal_create,
    "lower_primary": lower_primary,
    "middle_primary": middle_primary,
    "upper_primary": upper_primary,
    "lower_secondary": lower_secondary,
    "upper_secondary": upper_secondary,
    "undergraduate": undergraduate,
    "postgraduate": postgraduate
}

# Generate the final prompt based on user inputs
final_prompt = generate_final_prompt(user_input)

# Display the generated prompt
st.markdown("### Generated Prompt:")
st.text_area("Prompt", final_prompt, height=200)

# Submit button for clarity (optional)
if st.button("Submit"):
    st.success("Prompt generated successfully!")


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
