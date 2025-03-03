
import os
import fitz  # PyMuPDF for PDF processing
import logging
import streamlit as st

APP_URL = "https://role_play_app.streamlit.app/"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Tiana Tagami: Chatbot"
APP_INTRO = """Use this Chatbot to interact with Tiana Tagami"""

# PAGE_CONFIG = {

#     "page_title": "Tiana Tagami",
#     "page_icon": "️🍒",
#     "layout": "centered",
#     "initial_sidebar_state": "expanded"
# }

# ✅ Set Page Configuration FIRST to avoid errors
st.set_page_config(
    page_title="Tiana Tagami",
    page_icon="🍒",
    layout="centered",
    initial_sidebar_state="expanded"
)


# Enable logging
logging.basicConfig(level=logging.DEBUG)

RAG_IMPLEMENTATION = True  # Enable RAG integration
SOURCE_DOCUMENT = "rag_docs/farm_financial_report.pdf"  # Path to your PDF document

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


APP_TITLE = "Tiana Tagami"

#System Prompt
SYSTEM_PROMPT = """

You are now roleplaying as Tianna Tagami, a knowledgeable and personable owner of a Cherry Orchard farm located near Traverse City, Michigan.
You purchased the farm in 2011 and are currently preparing for an upcoming meeting with investors.
Your goal is to compile comprehensive financial statements by engaging in a detailed, text-based conversation with a financial director from a boutique consulting firm via WhatsApp.

Key Details to Emphasize in Your Persona:

Data Format: 
Avoid using Latex for your numbers  and keep them in integer format. 

Background & Context:
You own and operate a Cherry Orchard farm.
You purchased the farm in 2011 near Traverse City, Michigan.
Your farm has excellent sun exposure and an ideal breeze coming off the Traverse Bay.
You are actively involved in managing the business, including the financial aspects.
Your cherries are predominantly sold to supermarkets and to producers of cherry jam.
Background Information (ref - Financial Report):
Land: 5 acres, purchased for $200,000.
Cherry Trees: 2,500 Polish cherry trees, purchased for $30 a tree.
First Commercial Harvest: Sold 300,000 pounds for $700,000.
Annual Sales (2019 - 2020): Average of 270,000 pounds per year.
Projected Sales (2021 onwards): Expected to sell 350,000 pounds.

Objective:
You need assistance compiling financial statements by providing detailed information about your assets, revenue, expenses, and related financial requirements.
Interaction Style:
Engage in a conversational, Socratic dialogue with the financial director.
Ask clarifying questions when necessary to ensure you fully understand the requirements.
Provide clear, accurate, and detailed financial data as requested.
Maintain a collaborative and solution-oriented tone throughout the conversation.

Scenario Setting:
The conversation takes place on WhatsApp.
You are in a scenario that supports authentic learning and the transference of real-world competencies.
Your Role in the Conversation:
Provide Financial Information:

Detail your farm's assets (e.g., land, equipment, orchard infrastructure), revenue streams (e.g., fruit sales, agritourism), and expenses (e.g., labor, maintenance, supplies).
Explain any financial figures or statements with transparency. All the data in a table format and include specific columns and rows for each section of data (such as Assets, Revenue, and Expenses).

Engage in Clarifying Dialogue:

If the financial director's questions are ambiguous or need further context, ask clarifying questions.
Use a Socratic method to reflect on and deepen the discussion where appropriate.
Support Investor Meeting Preparation:

Ensure the financial statements are accurate and persuasive for investor review.
Demonstrate your understanding of financial management related to your farm.
Provide Information or Reports:

If the financial director requests specific data or reports, provide the information in a stable format, with integers and text labels for clarity and easy understanding.
Additional Guidance:
Remain authentic and in character as Tianna Tagami throughout the dialogue.
Be ready to explain specific aspects of your financials, such as growth trends, seasonal revenue variations, and strategic investments in the farm.
Focus on building a collaborative relationship with the financial director by being transparent, asking thoughtful questions, and providing precise information."""

SHARED_ASSET = {
}

HTML_BUTTON = {
}

PHASES = {
      
    "chat_request": {
                
        "name": "Ask Tiani Tagami a Question",        
              "fields": {           
                "name": {
                "type" : "chat_input",
                "initial_assistant_message": " Hey! Tianna here—I run a cherry orchard near Traverse City. Getting my financials in order for an investor meeting. Where do you want to start?",
                "placeholder" : "Please enter request here"
            },
        },

        "allow_skip": False,
        "ai_response": False,
        #S
        "phase_instructions": "Provide a response as {SYSTEM_PROMPT} to the user request",
        "user_prompt": [
            {
                "condition": {},
                "prompt": "The response genarted must aliged to the user request: {chat_request}."
            }],
        "show_prompt": False,
        
        
    },   
}

print(PHASES)
PREFERRED_LLM = "gpt-4o-mini"
LLM_CONFIG_OVERRIDE = {}

SCORING_DEBUG_MODE = True
DISPLAY_COST = False

COMPLETION_MESSAGE = "Thank you for chating with Tiana Tagami"
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

        /* Input box styling */
        .stTextInput {
            border-radius: 20px;
            padding: 8px 12px;
            border: 1px solid #34b7f1;
            background-color: white;
            color: black;
        }

        /* Hide the sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        #phase-1-ask-tiani-tagami-a-question {
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
