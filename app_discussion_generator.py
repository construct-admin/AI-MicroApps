import streamlit as st
import os
import hashlib

# configuration must be at the top.
st.set_page_config(
    page_title="Discussion Prompt Generator",
    page_icon="app_images/construct.webp",
    layout="centered",
    initial_sidebar_state="expanded"
)

### hash code function for the encryption
def hash_code(input_code):
    """Hashes the access code using SHA-256."""
    return hashlib.sha256(input_code.encode()).hexdigest()

### retrieve hash code 
ACCESS_CODE_HASH = os.getenv("ACCESS_CODE_HASH")

if not ACCESS_CODE_HASH:
    st.error("⚠️ Hashed access code not found. Please set ACCESS_CODE_HASH.")
    st.stop()

### Authentication Logic
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Access Restricted")
    access_code_input = st.text_input("Enter Access Code:", type="password")

    if st.button("Submit"):
        if hash_code(access_code_input) == ACCESS_CODE_HASH:
            st.session_state.authenticated = True
            st.rerun() 
        else:
            st.error("Incorrect access code. Please try again.")

    st.stop()  # Prevent unauthorized access


APP_URL = "https://discussion.streamlit.app"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Discussion Generator"
APP_INTRO = """Use this application to generate discussion forum questions."""

SYSTEM_PROMPT = """You are a discussion generator. Your goal is to develop structured discussion board prompts for online courses that align with user-provided learning objectives or content.

All discussion board prompts should contain the following:
1. **Discussion Questions**: Develop focused, open-ended questions that promote analysis and higher-order thinking. Include no more than 2 questions.
2. **Discussion Instructions**: Include:
   - Word count guidelines (e.g., initial post no more than 250 words).
   - Encouragement for learners to use personal experiences and academic references.
   - Instructions to respond to peers constructively while maintaining respect and professionalism.
3. **Conclusion**: Tie together the main points of the discussion and leave learners with a clear takeaway.

**Writing Style and Tone**:
- Writing should be clear, concise, and conversational.
- Use active voice.

**Training Material Example**:
Input:
- Learning Objective: "Describe the ethical considerations and transformative impact of AI in healthcare."
- Academic Stage: "Postgraduate"

Output:
**AI in Healthcare: Ethical Considerations**

Welcome to this week's discussion! Explore the ethical challenges and transformative impact of AI in healthcare. Engage in critical thinking to uncover how these technologies shape modern healthcare.

**Discussion Questions**:
1. What ethical challenges arise from AI's use in healthcare decision-making?
2. How can these challenges be addressed to ensure responsible innovation?

**Instructions**:
- Write an initial post (200-250 words) with one academic reference.
- Respond to two peers (minimum 100 words), providing constructive feedback and expanding their insights.
- Maintain professionalism and respect.

**Conclusion**:
This discussion will deepen your understanding of AI’s ethical considerations in healthcare.

Use this example as a reference to generate similar prompts.

"""

# Define phases and fields
PHASES = {
    "generate_discussion": {
        "name": "Discussion Prompt Generator",
        "fields": {
            "learning_objectives": {
                "type": "text_area",
                "label": "Enter the relevant module-level learning objective(s):",
                "height": 300
            },
            "learning_content": {
                "type": "text_area",
                "label": "Enter the relevant learning content:",
                "height": 500
            },
            "academic_stage_radio": {
                "type": "radio",
                "label": "Select the academic stage of the students:",
                "options": [
                    "Lower Primary",
                    "Middle Primary",
                    "Upper Primary",
                    "Lower Secondary",
                    "Upper Secondary",
                    "Undergraduate",
                    "Postgraduate"
                ]
            }
        },
        "phase_instructions": """
        Provide the relevant details (learning objectives, content, and academic stage) to generate a discussion prompt.
        """,
        "user_prompt": [
            {
                "condition": {},
                "prompt": "The discussion question should be aligned with the provided learning objectives: {learning_objectives}."
            },
            {
                "condition": {},
                "prompt": "The discussion question should be aligned with the following learning content: {learning_content}."
            },
            {
                "condition": {},
                "prompt": "Please align the discussion question to the following academic stage level: {academic_stage_radio}."
            }
        ],
        "ai_response": True,
        "allow_revisions": True,
        "show_prompt": True,
        "read_only_prompt": False
    }
}


PREFERRED_LLM = "gpt-4o"
LLM_CONFIG_OVERRIDE = {"gpt-4o": {
        "family": "openai",
        "model": "gpt-4o",
        "temperature": 0.5,
        "top_p": 0.85,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1
    }
}

SIDEBAR_HIDDEN = True

# Prompt builder
def build_user_prompt(user_input):
    """
    Dynamically build the user prompt with user-provided inputs.
    """
    try:
        # Retrieve inputs
        learning_objectives = user_input.get("learning_objectives", "").strip()
        learning_content = user_input.get("learning_content", "").strip()
        academic_stage = user_input.get("academic_stage_radio", "").strip()

        # Validate required inputs
        if not learning_objectives:
            raise ValueError("The 'Learning Objectives' field is required.")
        if not learning_content:
            raise ValueError("The 'Learning Content' field is required.")
        if not academic_stage:
            raise ValueError("An 'Academic Stage' must be selected.")

        # Build the user prompt
        user_prompt = [
            f"The discussion question should be aligned with the provided learning objective: {learning_objectives}.",
            f"The discussion question should be aligned with the following learning content: {learning_content}.",
            f"Please align the learning objectives to the following academic stage level: {academic_stage}."
        ]

        # Combine the prompts
        return "\n".join(user_prompt)

    except KeyError as e:
        raise ValueError(f"Missing key in user input: {e}")


### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))


# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())