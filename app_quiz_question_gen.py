import streamlit as st
import os
import hashlib

# configuration must be at the top.
st.set_page_config(
    page_title="Quiz Question Generator",
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


APP_URL = "https://quizquestion-generator.streamlit.app"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Quiz Question Generator"
APP_INTRO = """Use this application to generate quiz questions."""

SYSTEM_PROMPT = """System role:
You are an expert instructional designer who provides support in generating multiple-choice quiz questions. The questions should activate higher-order cognitive skills, and the feedback should support students to gauge their understanding.
- Each answer option must be on its own line.
- Maintain proper spacing between lines.

Output:
- Produce quiz questions that are aligned with required formatting as seen under examples.
- Align with corresponding learning objectives.
- If there is no feedback indicated within the example, there should be no feedback produced.
- If there is an asterisk indicating the correct answer within the example, there should always be an asterisk indicating the correct answer in your output.
- If there are alphabets indicating the options, do not repeat the alphabets and always follow alphabetical order.
- Follow example format exactly.

Constraints:
- Ensure that distractors are viable and that the question is not too easy to answer.
- Emphasize higher-level thinking.

Apply the formatting as seen in the examples below. Indicate the correct answer by using an asterisk.

Example output for each output format.

Selection: General Quiz Feedback
Which of the following is the weakest scatterer of conducting electrons?

A: Surface of the material.

B: Impurities in the material.

*C: Isotopes of the material.

D: Vibrating atoms within the material.

General Feedback: Isotopes have the least effect on electron scattering because they maintain the chemical properties of the original atoms, causing minimal disruption to the electron flow. This makes them the weakest scatterers among the options presented.

End of example for General Quiz Feedback

Selection: Answer-Option Level Quiz Feedback
Which of the following is the weakest scatterer of conducting electrons?

A: Surface of the material.

Feedback: Sorry, that is incorrect. The surface of a material can significantly scatter conducting electrons due to the abrupt change in the material's structure and the presence of surface states or defects. This is especially the case for ultra-small samples such as nanowires. However, Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons.

*B: Isotopes of the material.

Feedback: Correct! Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons. The slight difference in mass between isotopes typically has a minimal effect on electron scattering compared to other factors.

C: Impurities in the material.

Feedback: Sorry, that is incorrect. Impurities in a material are strong scatterers of conducting electrons. They introduce different potentials and disrupt the periodic lattice, leading to significant electron scattering. However, Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons.

D: Vibrating atoms within the material.

Feedback: Sorry, that is incorrect. Vibrating atoms, which are associated with lattice vibrations or phonons, can be significant scatterers of conducting electrons, especially at higher temperatures. However, Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons.

End of example for Answer-Option Level Quiz Feedback

Selection: Coursera Ungraded Quiz
Which of the following is the weakest scatterer of conducting electrons?

A: Surface of the material.

Feedback: Sorry, that is incorrect. The surface of a material can significantly scatter conducting electrons due to the abrupt change in the material's structure and the presence of surface states or defects. This is especially the case for ultra-small samples such as nanowires. However, Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons.

*B: Isotopes of the material.

Feedback: Correct! Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons. The slight difference in mass between isotopes typically has a minimal effect on electron scattering compared to other factors.

C: Impurities in the material.

Feedback: Sorry, that is incorrect. Impurities in a material are strong scatterers of conducting electrons. They introduce different potentials and disrupt the periodic lattice, leading to significant electron scattering. However, Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons.

D: Vibrating atoms within the material.

Feedback: Sorry, that is incorrect. Vibrating atoms, which are associated with lattice vibrations or phonons, can be significant scatterers of conducting electrons, especially at higher temperatures. However, Isotope atoms are chemically identical to the majority of atoms in the material and thus behave similarly in terms of interacting with electrons.

End of example for Coursera Ungraded Quiz

Selection: Coursera Graded Quiz
What is the threshold diameter below which the electrical conduction of a metal nanowire can become worse than that of the bulk?

A: The atomic distance of the metal.
Feedback: To learn more about the relationship between the diameter of metal nanowires and their electrical conduction properties, review “Resource Placeholder.”

*B: The electron mean free path in the metal.
Feedback: Correct, the electron mean free path in the metal is the threshold diameter.

C: The electron de Broglie wavelength in the metal.
Feedback: To learn more about the relationship between the diameter of metal nanowires and their electrical conduction properties, review “Resource Placeholder.”

D: The mean impurity distance in the metal.
Feedback: To learn more about the relationship between the diameter of metal nanowires and their electrical conduction properties, review “Resource Placeholder.”

End of example for Coursera Graded Quiz

Selection: H5P Textual Upload Feature
Who founded the Roman city of Barcino, which later became Barcelona?

The Greeks
*The Romans:::Barcelona was originally founded as a Roman colony named Barcino around the end of the 1st century BC.
The Visigoths
The Carthaginians

End of example for H5P Textual Upload Feature

Selection: Open edX OLX Quiz
>>Add the question text, or prompt, here. This text is required||You can add an optional tip or note related to the prompt like this. <<
( ) an incorrect answer {{You can specify optional feedback like this, which appears after this answer is submitted.}}
(x) the correct answer
( ) an incorrect answer {{You can specify optional feedback for none, a subset, or all of the answers.}}
||You can add an optional hint like this. Problems that have a hint include a hint button, and this text appears the first time learners select the button.||
||If you add more than one hint, a different hint appears each time learners select the hint button.||

End of example for Open edX OLX Quiz

Selection: NIC Quiz
Which of the following characteristics define the active adult segment according to NIC?

( )A. Rental properties that provide full meal services
( )B. Properties exclusively restricted to residents aged 62 years or older
( )C. Multifamily properties with limited lifestyle amenities
(x)D. Rental properties that are age-eligible, market-rate, and lifestyle focused, while excluding meal services

Correct: The definition of the Active Adult segment emphasizes age eligibility, market-rate rental, and lifestyle focus while excluding meal services.
Incorrect: Please review section 2.1: Defining the Segment, and try again.

End of example for NIC Quiz Feedback
"""

# Helper functions for dynamic conditions
def get_question_level_conditions():
    return [
        {"condition":{},"prompt":"Please align the learning objectives to the following academic stage level: \n Level:"},    
        {"condition": {"academic_stage_radio": "Lower Primary"}, "prompt": "Lower Primary."},
        {"condition": {"academic_stage_radio": "Middle Primary"}, "prompt": "Middle Primary."},
        {"condition": {"academic_stage_radio": "Upper Primary"}, "prompt": "Upper Primary."},
        {"condition": {"academic_stage_radio": "Lower Secondary"}, "prompt": "Lower Secondary."},
        {"condition": {"academic_stage_radio": "Upper Secondary"}, "prompt": "Upper Secondary."},
        {"condition": {"academic_stage_radio": "Undergraduate"}, "prompt": "Undergraduate."},
        {"condition": {"academic_stage_radio": "Postgraduate"}, "prompt": "Postgraduate."},
    ]

def get_output_format_conditions():
    return [
        {"condition": {"output_format": "General Quiz Feedback"}, "prompt": "Please align the output format according to the example provided for the selection General Quiz Feedback."},
        {"condition": {"output_format": "Answer-Option Level Quiz Feedback"}, "prompt": "Please align the output format according to the example provided for the selection Answer-Option Level Quiz Feedback."},
        {"condition": {"output_format": "Coursera Ungraded Quiz"}, "prompt": "Please align the output format according to the example provided for the selection Coursera Ungraded Quiz Feedback."},
        {"condition": {"output_format": "Coursera Graded Quiz"}, "prompt": "Please align the output format according to the example provided for the selection Coursera Graded Quiz."},
        {"condition": {"output_format": "H5P Textual Upload Feature"}, "prompt": "Please align the output format according to the example provided for the selection H5P Textual Upload Feature."},
        {"condition": {"output_format": "Open edX OLX Quiz"}, "prompt": "Please align the output format according to the example provided for the selection Open edX OLX Quiz."},
        {"condition": {"output_format": "NIC Quiz"}, "prompt": "Please align the output format according to the example provided for the selection NIC Quiz."},
    ]

# Define phases and fields
PHASES = {
    "generate_questions": {
        "name": "Generate Quiz Questions",
        "fields": {
            "title": {
                "type": "text_input",
                "label": "Enter the title of your module:",
            },
            "module_lo": {
                "type": "text_area",
                "label": "Enter the module learning objective(s):",
                "height": 200,
            },
            "questions_num": {
                "type": "slider",
                "label": "How many quiz questions would you like to generate?",
                "min_value": 1,
                "max_value": 10,
                "value": 3
            },
            "question_level": {
                "type": "radio",  # Changed to radio button
                "label": "Select the question level:",
                "options": [
                    "Lower Primary", "Middle Primary", "Upper Primary",
                    "Lower Secondary", "Upper Secondary",
                    "Undergraduate", "Postgraduate"
                ]
            },
            "output_format": {
                "type": "radio",  # Changed to radio button
                "label": "Select the output format:",
                "options": [
                    "General Quiz Feedback",
                    "Answer-Option Level Quiz Feedback",
                    "Coursera Ungraded Quiz",
                    "Coursera Graded Quiz",
                    "H5P Textual Upload Feature",
                    "Open edX OLX Quiz",
                    "NIC Quiz"
                ]
            },
            "correct_ans_num": {
                "type": "slider",
                "label": "Number of correct answers per question:",
                "min_value": 1,
                "max_value": 4,
                "value": 1
            },
            "distractors_num": {
                "type": "slider",
                "label": "Number of distractors per question:",
                "min_value": 1,
                "max_value": 3,
                "value": 1
            },
            "text_input": {
                "type": "text_area",
                "label": "Enter the text or context for the quiz questions:",
                "height": 500
            }
        },
        "phase_instructions": """
        Dynamically build the user prompt based on:
        - Number of questions
        - Selected question level
        - Selected output format
        """,
        "user_prompt": [
            {
                "condition": {},
                "prompt": "Please write {questions_num} multiple-choice question(s) for {question_level} level, each with {correct_ans_num} correct answer(s) and with {distractors_num} incorrect answers, based on the following text:\n{text_input}\n for {output_format}. Please align with the module title: {title} and the module learning objectives: {module_lo}."
            },
            {
                "condition": {"output_format": True},
                "prompt": "Align the questions with the {output_format} formatting.}"
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
    Build the user prompt dynamically based on user input.
    """
    try:
        # Retrieve the selected output format
        output_format = user_input.get("output_format", "")

        # Fetch the corresponding example from get_output_format_conditions
        output_conditions = get_output_format_conditions()
        example_text = next(
            (condition["prompt"] for condition in output_conditions if condition["condition"].get("output_format") == output_format),
            "No example available."
        )

        # Build the user prompt dynamically
        user_prompt_parts = [
            config["prompt"].format(**{
                key: user_input.get(key, ""),
                "example_text": example_text
            })
            for config in PHASES["generate_questions"]["user_prompt"]
            if all(user_input.get(key) == value for key, value in config["condition"].items())
        ]

        return "\n".join(user_prompt_parts)
    except KeyError as e:
        raise ValueError(f"Missing key in user input: {e}")

### Logout Button in Sidebar
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))

# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())