"""
Session state management for Visual Transcription app
"""
import streamlit as st
import os
import json

def initialize_session_state():
    """Initialize all session state variables with defaults."""
    # Authentication state
    st.session_state.setdefault("authenticated", False)
    
    # Prompt settings
    st.session_state.setdefault("max_words", "20")
    st.session_state.setdefault("prompt_category", "general")
    
    # Frame management
    st.session_state.setdefault("saved_frames", {})
    st.session_state.setdefault("saved_subtitles", [])
    st.session_state.setdefault("frame_index", 0)
    st.session_state.setdefault("frame_subtitle_map", {})
    st.session_state.setdefault("subtitles", {})
    st.session_state.setdefault("transcriptions", {})
    st.session_state.setdefault("inserted_transcriptions", set())
    
    # Video state
    st.session_state.setdefault("video", None)
    st.session_state.setdefault("frame_number", 0) 
    st.session_state.setdefault("total_frames", 0)
    st.session_state.setdefault("uploaded", False)
    
    # UI state
    st.session_state.setdefault("audio_transcript", [])
    st.session_state.setdefault("canvas_key", 0)
    st.session_state.setdefault("frame_increment", 1)
    st.session_state.setdefault("show_settings", True)
    st.session_state.setdefault("pending_video_file", None)
    st.session_state.setdefault("stroke_slider", 3)
    st.session_state.setdefault("stroke_color", "#00FF00")
    st.session_state.setdefault("active_tab", 0)  # 0=Settings, 1=Media Upload, 2=Visual Transcription
    st.session_state.setdefault("show_workspace", False)
    st.session_state.setdefault("prompt_categories", [])

def initialize_gpt4o_settings():
    """Initialize GPT-4o settings."""
    if "gpt-4o" not in st.session_state:
        try:
            # Initialize the gpt-4o dictionary with max_words
            st.session_state['gpt-4o'] = {
                "max_words": st.session_state["max_words"]
            }
            
            # Check if "General Purpose" prompt was loaded
            if "General Purpose" in st.session_state:
                # Get the prompt text that was loaded
                st.session_state['gpt-4o']["prompt"] = st.session_state["General Purpose"]
                st.session_state.prompt_category = "general"
            # Fall back to legacy path for backward compatibility
            elif os.path.exists(r"utils\chat_GPT.json"):
                with open(r"utils\chat_GPT.json", "r") as json_file:
                    gpt4o_data = json.load(json_file)
                    st.session_state['gpt-4o']["prompt"] = gpt4o_data.get("prompt", "").replace(
                        "%MAX_WORDS%", str(st.session_state["max_words"]))
                    st.session_state.prompt_category = "general"
            else:
                # Default fallback if no files found
                st.session_state['gpt-4o']["prompt"] = f"Describe the image in detail in no more than {st.session_state['max_words']} words."
                st.session_state.prompt_category = "general"
        except Exception as e:
            st.error(f"Error loading prompt settings: {e}")
            st.session_state['gpt-4o'] = {
                "prompt": f"Describe the image in detail in no more than {st.session_state['max_words']} words.",
                "max_words": st.session_state["max_words"]
            } 