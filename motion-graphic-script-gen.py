APP_URL = "https://mg-script-gen.streamlit.app"
APP_IMAGE = "construct.webp"
PUBLISHED = True

APP_TITLE = "Motion Graphic Script Generator"
APP_INTRO = """Use this application to generate motion graphic scripts."""

SYSTEM_PROMPT = """Develop and refine academic video scripts (750 - 800 words) for motion graphic videos that blend information and visuals to improve comprehension and retention.

Visuals: Incorporate advanced visual elements like 2.5D animations, high-quality renderings, and immersive simulations to transform static information into dynamic content. 

Output format:
Format scripts as a table, with columns for approximate time, text, and visual cues. Because we should have a change in visuals every 15 seconds, I create the script in 15 - 20-second increments, with each increment being a row in the table. You work on the assumption that each minute of video will have 120 words of text.

Scripts will include the following sections:
 1) Begin with an engaging hook. This may be a reference to a person, story, interesting statistic or case study, or a critical question from the content that should be engaged with.  Avoid pretext.  Usually, we don’t need to tell them what we’re going to talk about.  We can just start talking about it.  The pretext is different from a hook.  
 2) Following the introductory paragraph, add a paragraph that establishes the relevance of the learning material to real-world practices.
 3) Present the key theory or ideas of the content.
 4) Provide an explanation of how that links to solving the problems presented at the start.
 5) A conclusion that pulls the video together. The conclusion should tie together the main points explored in the script. It can be presented as key takeaways, or as thought-provoking questions for reflection. 

Language guide:
You'll need to closely match the writing samples, ensuring consistency and adherence to the specific requirements. This includes understanding the nuances of scriptwriting, such as pacing, dialogue, and narrative structure, tailored to an educational context. You will be provided with documents and samples to reference, and your responses should reflect the style and tone of these materials.
"""

RAG_IMPLEMENTATION = True  # Enable RAG
SOURCE_DOCUMENT = "rag_docs/ABETSIS_C1_M0_V1.pdf"  # The document to be used for RAG

# Import required libraries
import fitz  # PyMuPDF for extracting text from PDFs
from openai.embeddings_utils import get_embedding
import faiss
import numpy as np
import os

openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]

# Text Extraction
def extract_text_with_formatting(pdf_path):
    """
    Extracts text from a PDF file while preserving basic formatting.
    """
    document_text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            document_text += page.get_text("text")  # Extract text with basic formatting
    return document_text


# Embedding and Retrieval
def generate_embeddings(text_chunks):
    """
    Generate embeddings for a list of text chunks.
    """
    return [get_embedding(chunk, engine="text-embedding-ada-002") for chunk in text_chunks]


def create_faiss_index(embeddings):
    """
    Create a FAISS index for efficient similarity search.
    """
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype("float32"))
    return index


def retrieve_relevant_chunks(query, index, text_chunks, top_k=3):
    """
    Retrieve the most relevant text chunks for a given query using a FAISS index.
    """
    query_embedding = get_embedding(query, engine="text-embedding-ada-002")
    distances, indices = index.search(np.array([query_embedding]).astype("float32"), top_k)
    return [text_chunks[i] for i in indices[0]]


# Prompt Builder
def build_user_prompt(user_input):
    """
    Build the user prompt dynamically, integrating RAG-retrieved content.
    """
    try:
        # Extract user inputs
        learning_objectives = user_input.get("learning_objectives", "").strip()
        learning_content = user_input.get("learning_content", "").strip()
        academic_stage = user_input.get("academic_stage_radio", "").strip()
        query = learning_content or "General query"

        # Validate inputs
        if not learning_objectives:
            raise ValueError("The 'Learning Objectives' field is required.")
        if not academic_stage:
            raise ValueError("An 'Academic Stage' must be selected.")

        # Perform RAG if enabled
        retrieved_content = ""
        if RAG_IMPLEMENTATION:
            # Extract and process document content
            document_text = extract_text_with_formatting(SOURCE_DOCUMENT)
            text_chunks = document_text.split("\n\n")  # Split text into paragraphs
            embeddings = generate_embeddings(text_chunks)
            index = create_faiss_index(embeddings)
            retrieved_chunks = retrieve_relevant_chunks(query, index, text_chunks)
            retrieved_content = "\n".join(retrieved_chunks)

        # Construct the prompt
        prompt = f"""
        {SYSTEM_PROMPT}

        Learning Objectives: {learning_objectives}
        Academic Stage: {academic_stage}

        Retrieved Content:
        {retrieved_content}

        User Query:
        {query}
        """
        return prompt

    except Exception as e:
        raise ValueError(f"Error in building prompt: {e}")


# Example data for testing
PHASES = {
    "generate_discussion": {
        "name": "Motion Graphic Script Generator",
        "fields": {
            "learning_objectives": {
                "type": "text_area",
                "label": "Enter the relevant module-level learning objective(s):",
                "height": 500
            },
            "learning_content": {
                "type": "text_area",
                "label": "Enter relevant learning content that will serve as the basis for the motion graphic script.",
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
                "prompt": "The motion graphic should be aligned with the provided objectives: {learning_objectives}."
            },
            {
                "condition": {},
                "prompt": "Base the motion graphic script on the following content."
            },
            {
                "condition": {},
                "prompt": "Please align the learning objectives to the following academic stage level: {academic_stage_radio}."
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
}}

# Page configuration
PAGE_CONFIG = {
    "page_title": "Motion Graphic Script Generator",
    "page_icon": "app_images/construct.webp",
    "layout": "centered",
    "initial_sidebar_state": "expanded"
}

SIDEBAR_HIDDEN = True

# Entry point
from core_logic.main import main
if __name__ == "__main__":
    main(config=globals())
