"""
Visual Transcription Application - Main
"""
import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

# Import module functions
from authentication import check_password
from state_management import initialize_session_state, initialize_gpt4o_settings
from transcription import load_all_system_prompts, merge_transcripts
from file_handling import load_settings
from sidebar import render_sidebar
from settings_tab import render_settings_tab
from media_tab import render_media_tab
from workspace_tab import render_workspace_tab

def main():
    """Main function for the Visual Transcription application."""
    # Set page config
    st.set_page_config(
        page_title="VT Generator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize state
    initialize_session_state()
    
    # Check authentication
    if not check_password():
        return
    
    # Load environment variables
    load_dotenv()
    
    # Initialize OpenAI client
    api_key = os.getenv("PERSONAL_OPENAI_KEY")
    openai_client = OpenAI(api_key=api_key)
    
    # Load settings
    load_settings()
    
    # Initialize prompts
    initialize_gpt4o_settings()
    load_all_system_prompts()
    
    # App Header
    st.title("VT Generator - Visual Transcription")
    
    # Create tabs
    tab_titles = ["⚙️ Settings", "📋 Media Upload", "🎬 Visual Transcription"]
    settings_tab, media_tab, workspace_tab = st.tabs(tab_titles)
    
    # Render sidebar
    render_sidebar(openai_client, merge_transcripts)
    
    # Render tab content
    with settings_tab:
        render_settings_tab()
    
    with media_tab:
        render_media_tab()
    
    with workspace_tab:
        render_workspace_tab()

if __name__ == "__main__":
    main() 