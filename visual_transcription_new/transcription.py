"""
Transcription services for Visual Transcription app
"""
import os
import requests
import json
import streamlit as st
from PIL import Image
from openai import OpenAI
from image_processing import encode_image, get_frame_timestamp
import cv2

def load_all_system_prompts():
    """Load prompt templates from database/prompts directory."""
    try:
        path_to_prompts = os.path.join("database", "prompts")
        if not os.path.exists(path_to_prompts):
            # Try alternative path
            path_to_prompts = os.path.join("visual_transcription", "database", "prompts")
            if not os.path.exists(path_to_prompts):
                st.warning(f"Prompts directory not found at '{path_to_prompts}'. Using default values.")
                return
                
        # If we get here, the directory exists
        for file in os.listdir(path_to_prompts):
            if not file.endswith('.json'):
                continue
                
            try:
                with open(os.path.join(path_to_prompts, file), "r") as json_file:
                    json_data = json.load(json_file)
                    # Store the prompt text in session state using the name as the key
                    st.session_state[json_data["name"]] = json_data["prompt"].replace("%MAX_WORDS%", str(st.session_state["max_words"]))
            except Exception as file_error:
                st.warning(f"Error loading prompt file {file}: {file_error}")
    except Exception as e:
        st.warning(f"Error in load_all_system_prompts: {e}")
        # Continue execution even if loading fails

def transcribe_image(image_data, api_key):
    """Transcribe an image using OpenAI API."""
    try:
        # Use the saved frame data (numpy array) directly
        if image_data is None:
            st.error("No image data provided for transcription")
            return None

        # Get the image as base64 for OpenAI API
        img_pil = Image.fromarray(image_data)
        base64_image = encode_image(img_pil)
        
        # Use the GPT-4o prompt from settings
        prompt_text = st.session_state['gpt-4o'].get("prompt", "What's in this image?")
        prompt_category = st.session_state.get("prompt_category", "general")
        
        # Display which prompt is being used
        category_name_map = {
            "general": "General Purpose",
            "stem": "STEM",
            "humanities": "Humanities & Social Sciences",
            "business": "Business"
        }
        category_name = category_name_map.get(prompt_category, "Custom")
        
        # Show max tokens information
        max_tokens = int(st.session_state["max_words"]) * 4
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error transcribing image: {e}")
        return None

def merge_transcripts():
    """
    Creates a chronologically ordered combined transcript from both 
    audio subtitles and visual frame transcriptions.
    Returns a list of (timestamp, text, source_type) tuples sorted by timestamp.
    """
    try:
        combined_entries = []
        
        # Add entries from audio transcripts (subtitles)
        try:
            if "subtitles" not in st.session_state:
               pass
            else:
                for timestamp_key, text in st.session_state["subtitles"].items():
                    try:
                        # Skip empty text entries
                        if not text:
                            continue
                            
                        # Handle potential format issues with timestamp
                        try:
                            # Try to convert timestamp to float
                            if isinstance(timestamp_key, str):
                                timestamp = float(timestamp_key)
                            else:
                                timestamp = float(timestamp_key)
                                
                            combined_entries.append((timestamp, text, "audio"))
                        except (ValueError, TypeError) as time_error:
                            # If timestamp can't be converted to float, use a default
                            st.warning(f"Invalid timestamp format: {timestamp_key}. Using 0.0 instead. Error: {time_error}")
                            combined_entries.append((0.0, text, "audio"))
                    except Exception as entry_error:
                        st.warning(f"Error processing subtitle entry with timestamp {timestamp_key}: {entry_error}")
                        continue
        except Exception as subtitle_error:
            st.error(f"Error processing subtitles: {subtitle_error}")
        
        # Add entries from visual transcriptions
        try:
            has_transcriptions = "transcriptions" in st.session_state and st.session_state["transcriptions"]
            has_inserted = "inserted_transcriptions" in st.session_state and st.session_state["inserted_transcriptions"]
            
            if not has_transcriptions:
                pass
            elif not has_inserted:
                st.info("No visual transcriptions have been inserted into the transcript")
            else:
                # Get video object for timestamp conversion
                video_obj = st.session_state.get('video')
                
                if video_obj and video_obj.isOpened():
                    # Process with actual video timing
                    try:
                        for frame_number in st.session_state.inserted_transcriptions:
                            try:
                                if not isinstance(frame_number, int):
                                    # Try to convert if possible
                                    try:
                                        frame_number = int(frame_number)
                                    except (ValueError, TypeError):
                                        st.warning(f"Invalid frame number: {frame_number}")
                                        continue
                                        
                                if frame_number not in st.session_state["transcriptions"]:
                                    st.warning(f"Frame {frame_number} is marked as inserted but has no transcription")
                                    continue
                                    
                                transcription_text = st.session_state["transcriptions"][frame_number]
                                if not transcription_text:
                                    st.warning(f"Empty transcription for frame {frame_number}")
                                    continue
                                    
                                # Convert frame number to timestamp
                                try:
                                    timestamp = get_frame_timestamp(frame_number, video_obj)
                                    combined_entries.append((timestamp, transcription_text, "visual", frame_number))
                                except Exception as timestamp_error:
                                    st.warning(f"Error getting timestamp for frame {frame_number}: {timestamp_error}")
                                    # Use approximation
                                    fps = video_obj.get(cv2.CAP_PROP_FPS) or 30.0
                                    timestamp = float(frame_number) / fps
                                    combined_entries.append((timestamp, transcription_text, "visual", frame_number))
                            except Exception as frame_error:
                                st.warning(f"Error processing frame {frame_number}: {frame_error}")
                                continue
                    except Exception as process_error:
                        st.error(f"Error processing frames with video timing: {process_error}")
                else:
                    # If video isn't available, use placeholder timestamps
                    try:
                        st.warning("Video object not available, using approximate timestamps")
                        for frame_number in st.session_state.inserted_transcriptions:
                            try:
                                if frame_number in st.session_state["transcriptions"]:
                                    # Use frame number as approximate timestamp
                                    transcription = st.session_state["transcriptions"][frame_number]
                                    # Use 30fps as a default for approximation
                                    approximate_timestamp = float(frame_number) / 30.0
                                    combined_entries.append((approximate_timestamp, transcription, "visual", frame_number))
                            except Exception as frame_error:
                                st.warning(f"Error processing frame {frame_number} with approximate timing: {frame_error}")
                                continue
                    except Exception as approx_error:
                        st.error(f"Error processing frames with approximate timing: {approx_error}")
        except Exception as transcription_error:
            st.error(f"Error processing visual transcriptions: {transcription_error}")
        
        # Sort by timestamp (first element of each tuple)
        try:
            if not combined_entries:
                pass
                return []
                
            return sorted(combined_entries, key=lambda x: x[0])
        except Exception as sort_error:
            st.error(f"Error sorting merged entries: {sort_error}")
            return combined_entries  # Return unsorted if sorting fails
    except Exception as e:
        st.error(f"Unexpected error merging transcripts: {e}")
        return [] 