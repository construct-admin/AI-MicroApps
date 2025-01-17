import streamlit as st

# Set the page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="Learning Objectives Generator",
    page_icon="🔹",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Define the PHASES dictionary
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
        }
    }
}

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
    if phase_name == "generate_objectives":
        # Generate the main task based on `request_type`
        if user_input["request_type"] == "Provide learning objectives based on the content":
            prompt = (
                f"Please write {user_input['lo_quantity']} module learning objectives based on the provided content.\n"
            )
        elif user_input["request_type"] == "Suggest learning objectives based on the title":
            prompt = (
                f"Please suggest {user_input['lo_quantity']} module learning objectives for the provided title: {user_input.get('title', '')}.\n"
            )

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

        # Add relevance preferences
        if user_input.get("real_world_relevance"):
            prompt += "Try to provide learning objectives that are relevant to real-world practices and industry trends.\n"
        if user_input.get("problem_solving"):
            prompt += "Try to provide objectives that focus on problem-solving and critical thinking.\n"

        # Add academic stages
        stages = []
        if user_input.get("lower_primary"):
            stages.append("Lower Primary")
        if user_input.get("postgraduate"):
            stages.append("Postgraduate")
        if stages:
            prompt += f"Target the following academic stage(s): {', '.join(stages)}.\n"

    return prompt

# Simulate user input for testing
user_input = {
    "request_type": "Provide learning objectives based on the content",
    "lo_quantity": 3,
    "title": "Sample Title",
    "goal_apply": True,
    "real_world_relevance": True,
    "postgraduate": True,
}

# Call the function to generate the prompt
prompt = ""
generated_prompt = prompt_conditionals(prompt, user_input, phase_name="generate_objectives")

# Display the generated prompt for debugging
st.text_area("Generated Prompt", generated_prompt)

# Main entry point for the app
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
