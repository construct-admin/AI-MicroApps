
import os
import fitz  # type: ignore # PyMuPDF for PDF processing
import logging
import streamlit as st

APP_URL = "https://chat_support_tool.app/"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Canvas Converstaional: Chatbot"
APP_INTRO = ""


st.set_page_config(
    page_title="Canvas Support Support AI",
    page_icon="app_images/canvas_logo_single_mark_RwB_icon.ico",
    layout="centered",
    initial_sidebar_state="expanded"
)


# Enable logging
logging.basicConfig(level=logging.DEBUG)

RAG_IMPLEMENTATION = True  # Enable RAG integration
SOURCE_DOCUMENT = "rag_docs/Canvas_LMS_Training_Guide_for_AI_Conversational_Assistant.pdf"  # Path to your PDF document

# PDF Text Extraction Function
def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyMuPDF (fitz).
    """
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text("text")  # Extract plain text from each page
        logging.debug(f"Extracted text (first 500 chars): {text[:500]}") #Debugging: Print character from PDF.
        return text
    except Exception as e:
        logging.error(f"Error reading PDF: {str(e)}")
        return ""

def build_user_prompt(user_input):
    """
    Build the user prompt with user-provided input and document content.
    """
    try:
         # Validate required inputs        
        chat_request = user_input.get("chat_request", "").strip()
        
         # Debugging: Print retrieved values
        print("user chat_", chat_request)
        
        #check if Chat request is empty.         
        if not chat_request:
            raise ValueError("The 'Chat Request' field is required.")
        
        document_text = ""
        
        if RAG_IMPLEMENTATION and os.path.exists(SOURCE_DOCUMENT):
            document_text = extract_text_from_pdf(SOURCE_DOCUMENT)
            document_text = document_text.strip() if document_text else "" # Truncate text to fit within token limits
            st.write("Extracted text:", document_text)  # Corrected this line
            logging.debug("Document text extracted successfully.")
            
        user_prompt = f"""
        {SYSTEM_PROMPT}

        Example Template/Training Data:
        {document_text}
        """

        return user_prompt

    except Exception as e:
        logging.error(f"Error building prompt: {str(e)}")
        return ""


APP_TITLE = "Canvas Support Tool"

#System Prompt
SYSTEM_PROMPT = """You are a Canvas LMS expert assistant designed to help project teams understand, navigate, and manage the Canvas Learning Management System (LMS). You provide step-by-step guidance, troubleshooting solutions, and best practices for using Canvas efficiently.

Behavior Guidelines:

Be Clear & Concise: Provide direct, easy-to-follow instructions.

Context-Aware: Tailor responses based on the user’s role (Admin, Instructor, Student).

Problem-Solving First: Prioritize troubleshooting and actionable solutions.

Stay Conversational & Engaging: Use a friendly but professional tone.

Goal-Oriented: Focus on helping users accomplish tasks quickly and accurately.

Knowledge Scope:

Canvas Navigation & Features (Course creation, assignments, grading, quizzes, etc.)

User Roles & Permissions (Admin, Instructor, Student, Observer), consider permision that student have, instrtcors and students have in Cnvas LMS e.g students cant create assignements they can only take them unless they have a custom role.

Integrated Tools & Third-Party Apps (Google Drive, Turnitin, Zoom)

Troubleshooting & Support Best Practices"""

#Few short prompts with example of how you want the system to communicate with the user. 
FEW_SHORT_PROMPT = """ {
            "role": "user",
            "parts": [
                "Hi Canvas Assistant, I need help setting up my course."
            ],
        },
        {
            "role": "model",
            "parts": [
                "Hi! I'd be happy to help you set up your course. Are you an **instructor** creating a new course, or an **admin** setting up courses for multiple users?"
            ],
        },
        {
            "role": "user",
            "parts": [
                "I'm an instructor creating a new course."
            ],
        },
        {
            "role": "model",
            "parts": [
                "Great! You can create a new course by following these steps:\n\n"
                "1️) **Go to your Canvas Dashboard** and click **'Start a New Course'** (if enabled by your admin).\n"
                "2️) **Enter the Course Name** and adjust settings like the course term and visibility.\n"
                "3️) Click **'Create Course'** and you'll be taken to the course homepage.\n\n"
                "Would you like help organizing your course content with **modules and assignments**?"
            ],
        },
        {
            "role": "user",
            "parts": [
                "Hey, my students' grades aren't showing up in the Gradebook. What could be wrong?"
            ],
        },
        {
            "role": "model",
            "parts": [
                "I see! There are a few common reasons why grades might not appear. Let’s go through some checks:\n\n"
                "✅ **Is the assignment published?** - Only published assignments appear in the Gradebook.\n"
                "✅ **Is the assignment graded?** - If it's set to 'Not Graded,' it won’t show up.\n"
                "✅ **Are there grade posting policies enabled?** - Check if grades are manually hidden.\n"
                "✅ **Did students submit work?** - If no submissions exist, grades won’t populate.\n\n"
                "Try these steps, and let me know if you need further troubleshooting!"
            ],
        },
        {
            "role": "user",
            "parts": [
                "I need to add a new TA to my Canvas course. How do I do that?"
            ],
        },
        {
            "role": "model",
            "parts": [
                "No problem! Here’s how you can add a **Teaching Assistant (TA)** to your course:\n\n"
                "1️) **Go to your course** and click on **'People'** in the navigation menu.\n"
                "2️) Click **'+ People'** in the top right.\n"
                "3️) Enter the **TA’s email address**.\n"
                "4️) In the **Role** dropdown, select **'TA'**.\n"
                "5️) Click **'Next'**, then **'Add User'**.\n\n"
                "The TA will receive an email invitation to join your course. Let me know if you need help managing their permissions!"
            ],
        },
        {
            "role": "user",
            "parts": [
                "How do I create a quiz that auto-grades student responses?"
            ],
        },
        {
            "role": "model",
            "parts": [
                "Great question! Canvas allows you to create auto-graded quizzes using multiple-choice or true/false questions. Here’s how:\n\n"
                "1️) **Go to Quizzes** in your course navigation.\n"
                "2️) Click **'+ Quiz'** and choose **'New Quizzes'**.\n"
                "3️) Click **'Build'** to start adding questions.\n"
                "4️) Select **Multiple Choice, True/False, or Fill-in-the-Blank** (these can be auto-graded).\n"
                "5️) Set **correct answers** and **point values**.\n"
                "6️) Click **'Save & Publish'** when you're done!\n\n"
                "Do you also want to set up **time limits or multiple attempts** for your quiz?"
            ],
        },
        {
            "role": "user",
            "parts": [
                "How can I check my course from a student's perspective?"
            ],
        },
        {
            "role": "model",
            "parts": [
                "You can use **Student View** to preview how your course looks for students. Here’s how:\n\n"
                "1️) **Go to 'Course Settings'** in the left navigation menu.\n"
                "2️) Click the **'Student View'** button on the right.\n"
                "3️) Navigate through the course as a student would.\n\n"
                " *You can even submit assignments and take quizzes in this mode!* When you're done, click **'Leave Student View'** to return to your instructor role.\n\n"
                "Would you like help testing a specific feature, like quizzes or discussions?"
            ],
        }"""

SHARED_ASSET = {
}

HTML_BUTTON = {
}

PHASES = {
      
    "chat_request": {
                
        "name": "get input",        
              "fields": {           
                "name": {
                "type" : "chat_input",
                "initial_assistant_message": "Hey there how can I assist you today?"
            },
        },

        "allow_skip": False,
        "ai_response": False,
        #S
        "phase_instructions": "Provide a response as to the user request as {SYSTEM_PROMPT} using {FEW_SHORT_PROMPT} AS few short prompt",
        "user_prompt": [
            {
                "condition": {},
                "prompt": "The response genarted must aliged to the user request: {chat_request} and follow the format {FEW_SHORT_PROMPT}."
            }],
        "show_prompt": False,
        
        
    },   
}

print(PHASES)
PREFERRED_LLM = "GPT-4.5"
LLM_CONFIG_OVERRIDE = {}

SCORING_DEBUG_MODE = True
DISPLAY_COST = False

COMPLETION_MESSAGE = "Thank you for chatting with Canvas Assistant AI."
COMPLETION_CELEBRATION = False

st.markdown(
    """
<style>
        /* WhatsApp Light Background */
        .stApp {
            background-color: #eae6df;
            font-family: 'Arial', sans-serif;
        }

        /* Messages container */
        .stChatMessage {
            padding: 10px 15px;
            border-radius: 18px;
            max-width: 75%;
            margin-bottom: 8px;
        }

        /* User messages (light green bubbles) */
        .stChatMessage:nth-child(even) {
            background-color: #dcf8c6;
            color: black;
            align-self: flex-end;
        }

        /* AI messages (white bubbles) */
        .stChatMessage:nth-child(odd) {
            background-color: white;
            color: black;
            align-self: flex-start;
            border: 1px solid #d1d7db;
        }
        /* Hide the sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        #phase-1-get-input {
            display: none;
        }
        }

    </style>
    """,
    unsafe_allow_html=True
)


SIDEBAR_HIDDEN = True

from core_logic.main import main
if __name__ == "__main__":    
    main(config=globals())
