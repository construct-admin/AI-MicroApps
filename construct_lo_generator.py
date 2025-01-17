import streamlit as st

# Set the page configuration
st.set_page_config(
    page_title="Learning Objectives Generator",
    page_icon="🔹",
    layout="centered",
    initial_sidebar_state="expanded"
)

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

# Dynamically build the AI prompt based on user input
def prompt_conditionals(user_input):
    """
    Generate the AI prompt dynamically based on user input.
    """
    prompt = ""

    # Add the main request type prompt
    if user_input.get("request_type") == "Provide learning objectives based on the course learning objectives":
        prompt = f"Please write {user_input['lo_quantity']} module learning objectives based on the provided course-level learning objectives: {user_input.get('course_lo', '')}.\n"
    elif user_input.get("request_type") == "Suggest learning objectives based on the title":
        prompt = f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input.get('title', '')}.\n"
    elif user_input.get("request_type") == "Provide learning objectives based on the graded assessment question(s) of the module":
        prompt = f"Please suggest {user_input['lo_quantity']} module learning objectives based on the graded quiz questions: {user_input.get('quiz_lo', '')}.\n"
    elif user_input.get("request_type") == "Provide learning objectives based on the formative activity questions":
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

# Simulate user input for testing purposes
user_input = {
    "request_type": "Provide learning objectives based on the course learning objectives",
    "course_lo": "Sample course objective",
    "lo_quantity": 3,
    "goal_apply": True,
    "goal_evaluate": False,
    "goal_analyze": True,
    "real_world_relevance": True,
    "problem_solving": True,
    "meta_cognitive_reflection": False,
    "ethical_consideration": True,
    "lower_primary": False,
    "middle_primary": False,
    "upper_primary": False,
    "lower_secondary": False,
    "upper_secondary": True,
    "undergraduate": False,
    "postgraduate": True,
}

# Generate the prompt based on user input
generated_prompt = prompt_conditionals(user_input)

# Display the generated prompt in Streamlit
st.text_area("Generated Prompt", generated_prompt)

# Example submission button to test
if st.button("Submit"):
    st.write("Prompt successfully generated!")
