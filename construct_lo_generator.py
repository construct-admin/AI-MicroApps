import streamlit as st

# Set the page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="Learning Objectives Generator",
    page_icon="🔹",
    layout="centered",
    initial_sidebar_state="expanded"
)

# App-level metadata
PUBLISHED = True
APP_URL = "https://construct-lo-generator.streamlit.app"
APP_IMAGE = "lo_builder_flat.webp"

# Application title and description
APP_TITLE = "Learning Objectives Generator"
APP_INTRO = """
This application is based on constructive alignment principles. It allows you to generate learning objectives that align with your course-level learning objectives, assessments, and activities. Furthermore, it can be used to enhance existing learning objectives and validate objective alignment.
"""

# Instructions for how the app works
APP_HOW_IT_WORKS = """
1. Provide details about your course/module.
2. Select cognitive goals and relevance preferences.
3. Generate specific, measurable, and aligned learning objectives.
"""

# Function to dynamically generate the AI prompt
def prompt_conditionals(prompt, user_input, phase_name=None):
    """
    Dynamically build the AI prompt based on user input and phase.
    Arguments:
        - prompt: (str) Base prompt to modify.
        - user_input: (dict) Dictionary containing user input fields.
        - phase_name: (str) Name of the current phase (e.g., 'generate_objectives').
    Returns:
        - Modified prompt string.
    """
    # Check the phase and generate the prompt accordingly
    if phase_name == "generate_objectives":
        # Start with the main task based on `request_type`
        if user_input["request_type"] == "Validate alignment between learning content and objectives":
            prompt = (
                "Please validate the alignment between the provided learning content and the learning objectives provided.\n"
                + "Be extremely strict and make sure that A) specific content exists that can be assessed to meet the learning objective and B) the learning objective is reasonable for an online course.\n"
            )
            if user_input.get("learning_objectives"):
                prompt += (
                    "Here are my learning objectives: \n"
                    + user_input["learning_objectives"] + "\n"
                )
            if user_input.get("learning_content"):
                prompt += (
                    "Here is the content: \n"
                    + "===============\n"
                    + user_input["learning_content"] + "\n"
                )
        elif user_input["request_type"] == "Suggest learning objectives based on the title":
            prompt = (
                f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input.get('title', '')}.\n"
            )
        elif user_input["request_type"] == "Provide learning objectives based on the content":
            prompt = (
                f"Please write {user_input['lo_quantity']} module learning objectives based on the provided content.\n"
            )

        # Add cognitive goals (Bloom's Taxonomy)
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

        # Add relevance preferences
        if user_input.get("real_world_relevance"):
            prompt += "Try to provide learning objectives that are relevant to real-world practices and industry trends.\n"
        if user_input.get("problem_solving"):
            prompt += "Try to provide objectives that focus on problem-solving and critical thinking.\n"
        if user_input.get("meta_cognitive_reflection"):
            prompt += "Try to provide objectives that focus on meta-cognitive reflections.\n"
        if user_input.get("ethical_consideration"):
            prompt += "Try to provide objectives that include emotional, moral, and ethical considerations.\n"

        # Add academic stages
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

    # Add logic for other phases if needed in the future
    elif phase_name == "another_phase":
        prompt += "This is another phase-specific prompt logic.\n"

    # Return the dynamically generated prompt
    return prompt

# Simulated user input for debugging purposes
user_input = {
    "request_type": "Provide learning objectives based on the content",
    "lo_quantity": 4,
    "title": "Introduction to Marketing",
    "learning_content": "Content about marketing principles and strategies.",
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

# Initialize the prompt (empty at the start)
prompt = ""

# Generate the prompt dynamically for the "generate_objectives" phase
final_prompt = prompt_conditionals(prompt, user_input, phase_name="generate_objectives")

# Display the generated prompt in Streamlit for debugging
st.text_area("Generated Prompt", final_prompt)

# Example submit button to finalize the process
if st.button("Submit"):
    st.success("Prompt successfully generated!")
    st.write(final_prompt)



# Main entry point for the app
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
