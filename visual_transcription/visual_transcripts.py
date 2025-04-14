import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import base64
import requests
import json
import glob
from PIL import Image
from openai import OpenAI
from docx import Document
from streamlit_drawable_canvas import st_canvas
from dotenv import load_dotenv

# Set Streamlit theme - Must be the first Streamlit command
st.set_page_config(page_title="VT Generator", page_icon="🖼️", layout="wide")
load_dotenv()

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    
if "max_words" not in st.session_state:
    st.session_state["max_words"] = "20"
    
if "prompt_category" not in st.session_state:
    st.session_state.prompt_category = "general"

def load_all_system_prompts():
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

# Add password authentication
def check_password():
    """Returns True if the password is correct, False otherwise."""
    # If already authenticated, return True
    if st.session_state.authenticated:
        return True
    
    # Create login form
    st.title("VT Generator - Authentication Required")
    st.markdown("### Please enter your password to continue")
    st.markdown("This application requires authentication to access its functionality.")
    
    # Create columns for centered form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        password = st.text_input("Password:", type="password", key="password_input")
        login_button = st.button("Login", key="login_button", type="primary")
        
        # Verify password
        if login_button or password:
            if password == "pRoV3rsity!!@2024":
                st.session_state.authenticated = True
                st.success("Authentication successful! Loading application...")
                st.experimental_rerun()
                return True
            else:
                st.error("Incorrect password. Please try again.")
                return False
    
    return False

# Check authentication before showing the main application
if not check_password():
    st.stop()  # Stop execution here if not authenticated

# Initialize OpenAI client
GPT_API_KEY = os.getenv("PERSONAL_OPENAI_KEY")
client = OpenAI(api_key=GPT_API_KEY)

# --- Helper Functions ---
# The line below was causing a NameError - removing or properly commenting it

# Define minimal fallback functions if needed
def image_to_base64(image):
    """Convert PIL image or numpy array to base64 string."""
    try:
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        image.save(buffered, format="JPEG")
        with open(buffered.name, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        st.error(f"Error converting image to base64: {e}")
        # Return empty string or placeholder in case of error
        return ""

def get_frame_timestamp(frame_number, video_obj):
    """Get timestamp for a frame."""
    try:
        if video_obj and video_obj.isOpened():
            fps = video_obj.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                seconds = frame_number / fps
                return seconds
        return 0
    except Exception as e:
        st.warning(f"Error getting frame timestamp: {e}")
        return 0

# Function to encode image as base64
def encode_image(image):
    try:
        buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        image.save(buffered, format="JPEG")
        with open(buffered.name, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        st.error(f"Error encoding image: {e}")
        return ""

# Function to convert seconds to HH:MM:SS format
def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    try:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        st.warning(f"Error converting seconds to timestamp: {e}")
        return "00:00:00"

# Function to parse SRT files
def parse_srt(file):
    try:
        subtitles = {}
        lines = file.read().decode("utf-8").split("\n")
        index, start_time = None, None
        for line in lines:
            try:
                line = line.strip()
                if line.isdigit():
                    index = int(line)
                elif "-->" in line:
                    start_time = line.split(" --> ")[0]
                    start_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(start_time.replace(',', '.').split(':'))))
                elif line:
                    if index is not None and start_time is not None:
                        subtitles[start_time] = line
            except Exception as line_error:
                # If a single line fails to parse, log it but continue with the rest
                st.warning(f"Error parsing subtitle line: {line_error}")
                continue
        return subtitles
    except Exception as e:
        st.error(f"Error parsing SRT file: {e}")
        return {}

# --- Cropping Logic Functions ---
def crop_rectangular(image_cv_bgr, rect_data):
    """Crops the OpenCV BGR image using rectangle data."""
    try:
        left = int(rect_data['left'])
        top = int(rect_data['top'])
        width = int(rect_data['width'])
        height = int(rect_data['height'])
        if width <= 0 or height <= 0:
            st.warning("Please draw a valid rectangle.")
            return None
        h_img, w_img = image_cv_bgr.shape[:2]
        x1, y1 = max(0, left), max(0, top)
        x2, y2 = min(w_img, left + width), min(h_img, top + height)
        if x2 <= x1 or y2 <= y1:
             st.warning("Calculated crop area is outside image bounds or invalid.")
             return None
        cropped_bgr = image_cv_bgr[y1:y2, x1:x2]
        return cropped_bgr
    except Exception as e:
        st.error(f"Error during rectangular cropping: {e}")
        return None

def crop_freeform(image_cv_bgr, path_data):
    """Crops the OpenCV BGR image using freeform path data."""
    if not path_data:
         st.warning("Received empty path data.")
         return None
    
    # Get image dimensions for boundary validation
    h_img, w_img = image_cv_bgr.shape[:2]
    
    points_list = []
    for point_cmd in path_data:
        if len(point_cmd) >= 3:
            try:
                # Extract coordinates
                x = int(float(point_cmd[-2]))
                y = int(float(point_cmd[-1]))
                
                # Clip coordinates to image boundaries
                x = max(0, min(x, w_img - 1))
                y = max(0, min(y, h_img - 1))
                
                # Add the valid point to our list
                points_list.append([x, y])
            except (ValueError, IndexError, TypeError):
                # Skip invalid point data silently
                continue

    # Ensure we have enough points to form a shape
    if len(points_list) < 3:
         st.warning("Not enough valid points to create a crop area. Please try again.")
         return None
    
    try:
        # Convert to numpy array for OpenCV
        contour = np.array(points_list, dtype=np.int32)
        
        # Create a mask with only the points inside the image
        mask = np.zeros(image_cv_bgr.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, color=255, thickness=cv2.FILLED)
        
        # Apply the mask
        masked_image_bgr = cv2.bitwise_and(image_cv_bgr, image_cv_bgr, mask=mask)
        
        # Calculate bounding rectangle
        x_bb, y_bb, w_bb, h_bb = cv2.boundingRect(contour)
        
        # Validate bounding box dimensions
        if w_bb <= 0 or h_bb <= 0:
            st.warning("Freeform crop area resulted in an empty image. Please try a larger selection.")
            return None
            
        # Ensure bounding box is within image boundaries
        x_bb = max(0, x_bb)
        y_bb = max(0, y_bb)
        w_bb = min(w_bb, w_img - x_bb)
        h_bb = min(h_bb, h_img - y_bb)
        
        # Final validation of crop area
        if w_bb <= 0 or h_bb <= 0:
            st.warning("Crop area is outside image boundaries. Please try again.")
            return None
            
        # Extract the bounded region
        cropped_bgr = masked_image_bgr[y_bb:y_bb+h_bb, x_bb:x_bb+w_bb]
        return cropped_bgr
    
    except Exception as e:
        st.error(f"Error during freeform cropping: {e}")
        return None

# Function to get list of users from the database directory
def get_settings():
    """Load default settings from file if available, otherwise return defaults"""
    settings_path = "visual_transcription/database/default.json"
    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                
            # Load navigation settings
            if 'frame_increment' in settings:
                st.session_state.frame_increment = settings['frame_increment']
                
            # Load drawing settings
            if 'stroke_slider' in settings:
                st.session_state.stroke_slider = settings['stroke_slider']
            if 'stroke_color' in settings:
                st.session_state.stroke_color = settings['stroke_color']
    except Exception as e:
        st.error(f"Error loading settings: {e}")
        # Use defaults if settings can't be loaded

def save_settings():
    """Save current settings to default file"""
    try:
        # Create the directory if it doesn't exist
        os.makedirs("visual_transcription/database", exist_ok=True)
        
        settings_path = "visual_transcription/database/default.json"
        
        # Create a settings dictionary with just navigation and drawing settings
        settings = {
            'frame_increment': st.session_state.get('frame_increment', 1),
            'stroke_slider': st.session_state.get('stroke_slider', 3),
            'stroke_color': st.session_state.get('stroke_color', '#00FF00')
        }
        
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        return True
    except Exception as e:
        st.error(f"Error saving settings: {e}")
        return False

# Download full transcript
def download_transcript():
    try:
        doc = Document()
        doc.add_heading("Visual Transcript", level=1)
        
        # Use the merged transcripts for a more comprehensive document
        try:
            merged_transcripts = merge_transcripts()
        except Exception as e:
            st.error(f"Error merging transcripts: {e}")
            merged_transcripts = []
        
        if merged_transcripts:
            # Add a section explaining the format
            doc.add_paragraph("This document contains both audio transcripts and visual descriptions in chronological order.")
            doc.add_paragraph("Timestamps are shown in HH:MM:SS format.")
            
            # Add all merged transcripts in chronological order
            for entry in merged_transcripts:
                try:
                    if len(entry) == 3:  # Audio entry (timestamp, text, "audio")
                        timestamp, text, source = entry
                        formatted_time = seconds_to_timestamp(timestamp)
                        para = doc.add_paragraph()
                        para.add_run(f"[{formatted_time}] ").bold = True
                        para.add_run(f"{text}")
                    else:  # Visual entry (timestamp, text, "visual", frame_number)
                        timestamp, text, source, frame_number = entry
                        formatted_time = seconds_to_timestamp(timestamp)
                        para = doc.add_paragraph()
                        para.add_run(f"[{formatted_time} - Frame {frame_number}] ").bold = True
                        para.add_run(f"Visual Description: {text}").italic = True
                except Exception as entry_error:
                    st.warning(f"Error processing transcript entry: {entry_error}")
                    continue
        else:
            # Fall back to original subtitles if no merged transcripts
            for timestamp, text in st.session_state.get("subtitles", {}).items():
                try:
                    formatted_time = seconds_to_timestamp(float(timestamp))
                    doc.add_paragraph(f"{formatted_time}: {text}")
                except (ValueError, TypeError) as time_error:
                    # Handle timestamp conversion errors
                    st.warning(f"Error with timestamp {timestamp}: {time_error}")
                    doc.add_paragraph(f"{timestamp}: {text}")
                except Exception as para_error:
                    st.warning(f"Error adding paragraph: {para_error}")
                    continue
        
        try:
            temp_doc_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
            doc.save(temp_doc_path)
            with open(temp_doc_path, "rb") as doc_file:
                st.sidebar.download_button("Download Transcript", doc_file, file_name="visual_transcript.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as save_error:
            st.error(f"Error saving transcript document: {save_error}")
    except Exception as e:
        st.error(f"Error creating transcript document: {e}")

# Function to merge audio and visual transcripts chronologically
def merge_transcripts():
    """
    Creates a chronologically ordered combined transcript from both 
    audio subtitles and visual frame transcriptions.
    Returns a list of (timestamp, text, source_type) tuples sorted by timestamp.
    """
    try:
        combined_entries = []
    
        # Add entries from audio transcripts (subtitles)
        if st.session_state.get("subtitles"):
            for timestamp, text in st.session_state["subtitles"].items():
                # Handle potential format issues
                try:
                    combined_entries.append((float(timestamp), text, "audio"))
                except (ValueError, TypeError) as time_error:
                    # If timestamp can't be converted to float, use a default
                    st.warning(f"Invalid timestamp format: {timestamp}. Using 0.0 instead.")
                    combined_entries.append((0.0, text, "audio"))
        
        # Add entries from visual transcriptions
        if st.session_state.get("transcriptions") and st.session_state.get("inserted_transcriptions"):
            # Get video object for timestamp conversion
            video_obj = st.session_state.get('video')
            if video_obj and video_obj.isOpened():
                for frame_number in st.session_state.inserted_transcriptions:
                    try:
                        if frame_number in st.session_state["transcriptions"]:
                            # Convert frame number to timestamp
                            timestamp = get_frame_timestamp(frame_number, video_obj)
                            transcription = st.session_state["transcriptions"][frame_number]
                            combined_entries.append((timestamp, transcription, "visual", frame_number))
                    except Exception as frame_error:
                        st.warning(f"Error processing frame {frame_number}: {frame_error}")
                        continue
            else:
                # If video isn't available, use placeholder timestamps
                for frame_number in st.session_state.inserted_transcriptions:
                    try:
                        if frame_number in st.session_state["transcriptions"]:
                            # Use frame number as approximate timestamp
                            transcription = st.session_state["transcriptions"][frame_number]
                            combined_entries.append((float(frame_number)/30.0, transcription, "visual", frame_number))
                    except Exception as frame_error:
                        st.warning(f"Error processing frame {frame_error}")
                        continue
        
        # Sort by timestamp (first element of each tuple)
        return sorted(combined_entries, key=lambda x: x[0])
    except Exception as e:
        st.error(f"Error merging transcripts: {e}")
        return []

# Initialize session state variables
# Original session state variables
st.session_state.setdefault("saved_frames", {})
st.session_state.setdefault("saved_subtitles", [])
st.session_state.setdefault("frame_index", 0)
st.session_state.setdefault("frame_subtitle_map", {})
st.session_state.setdefault("subtitles", {})
st.session_state.get("subtitles", {})
st.session_state.setdefault("transcriptions", {})
# New session state to track which transcriptions have been inserted into the transcript
st.session_state.setdefault("inserted_transcriptions", set())

# Additional session state for enhanced features
st.session_state.setdefault("video", None)
st.session_state.setdefault("frame_number", 0)
st.session_state.setdefault("total_frames", 0)
st.session_state.setdefault("uploaded", False)
st.session_state.setdefault("audio_transcript", [])
st.session_state.setdefault("canvas_key", 0)
st.session_state.setdefault("frame_increment", 1)
st.session_state.setdefault("show_settings", True)
st.session_state.setdefault("pending_video_file", None)
st.session_state.setdefault("stroke_slider", 3)
st.session_state.setdefault("stroke_color", "#00FF00")
# Add active tab tracking
st.session_state.setdefault("active_tab", 0)  # 0=Settings, 1=Media Upload, 2=Visual Transcription
# Add flag for showing workspace after video processing
st.session_state.setdefault("show_workspace", False)
st.session_state.get("prompt_categories", [])

load_all_system_prompts()

# Try to load settings
get_settings()

# GPT-4o settings
if "gpt-4o" not in st.session_state:
    try:
        # Initialize the gpt-4o dictionary with max_words
        st.session_state['gpt-4o'] = {
            "max_words": st.session_state["max_words"]
        }
        
        # Check if "General Purpose" prompt was loaded by load_all_system_prompts
        if "General Purpose" in st.session_state:
            # Get the prompt text that was loaded by load_all_system_prompts
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

# Sidebar setup
st.sidebar.title("Saved Frames & Transcripts")
# The sidebar content will be updated later in the file

# --- App Title and Initial Setup ---
st.title('Video Transcription Service with Cropping')

# Create three main tabs for the entire application
tab_names = ["Configuration Settings", "Media Upload", "Visual Transcription"]
settings_tab, media_tab, workspace_tab = st.tabs(tab_names)

# If we just processed a video, we need to navigate to the workspace tab
# This is done using the show_workspace flag in session state
if st.session_state.show_workspace and st.session_state.uploaded:
    # Reset the flag so we don't keep redirecting
    st.session_state.show_workspace = False
    # Put the Visual Transcription tab content directly here to display first
    st.warning("Video processed! Navigating to Visual Transcription tab...")
    # Using rerun often causes issues with tab selection, so instead we'll
    # create a message instructing the user
    st.success("Please click on the 'Visual Transcription' tab to view your video.")

# -----------------------------------------------
# TAB 1: CONFIGURATION SETTINGS
# -----------------------------------------------
with settings_tab:
    # Navigation Settings
    st.subheader("Navigation Settings")
    # Frame increment input
    increment_value = st.number_input(
        'Frame increment (number of frames to jump when using navigation buttons)',
        min_value=1,
        max_value=100,
        value=st.session_state.frame_increment,
        step=1,
        key='increment_input'
    )
    # Update session state with the new increment value
    if increment_value != st.session_state.frame_increment:
        st.session_state.frame_increment = int(increment_value)
        st.success(f"Frame increment updated to {st.session_state.frame_increment}")
    
    # st.markdown("---")
    
    # # Drawing Settings
    # st.subheader("Drawing Settings")
    # # Add drawing settings
    # # Add stroke width slider
    # stroke_width = st.slider("Stroke width:", 1, 25, st.session_state.stroke_slider, key='stroke_width_input')
    # if stroke_width != st.session_state.stroke_slider:
    #     st.session_state.stroke_slider = stroke_width
        
    # # Add color picker for stroke color
    # stroke_color = st.color_picker("Stroke color:", st.session_state.stroke_color, key='stroke_color_input')
    # if stroke_color != st.session_state.stroke_color:
    #     st.session_state.stroke_color = stroke_color
    
    st.markdown("---")
    
    # GPT-4o Settings
    st.subheader("GPT-4o Settings")
    # Display and allow editing of the max words
    prev_max_words = str(st.session_state['gpt-4o'].get("max_words", "100"))
    max_words_input = st.text_input(
        label="Max words for description",
        value=prev_max_words,
        key='gpt4_max_words'
    )
    current_max_words = str(max_words_input)
    st.session_state["max_words"] = current_max_words

    # Update prompt if max_words changed
    current_prompt = st.session_state['gpt-4o'].get("prompt", "Describe the image in %MAX_WORDS% words.")
    if prev_max_words != current_max_words:
        st.session_state['gpt-4o']["prompt"] = current_prompt.replace(f"{prev_max_words}", f"{current_max_words}")
        st.session_state['gpt-4o']["max_words"] = current_max_words
        current_prompt = st.session_state['gpt-4o']["prompt"]
    
    # Save settings button
    st.markdown("---")
    if st.button("Save Configuration", key="save_config_button"):
        if save_settings():
            st.success("Settings saved successfully")

# -----------------------------------------------
# TAB 2: MEDIA UPLOAD
# -----------------------------------------------
with media_tab:
    # Audio Transcript
    st.subheader("Audio Transcript")
    # Load Audio Transcript if not already loaded
    if not st.session_state.audio_transcript:
        # Replace the old uploader with the SRT file uploader
        srt_file = st.file_uploader("Upload Subtitle File (SRT)", type=["srt"], key='srt_uploader')
        if srt_file is not None:
            # Process SRT file immediately if video already loaded 
            if st.session_state.get('uploaded', False) and st.session_state.get('video') is not None:
                try:
                    # Save current transcriptions and inserted_transcriptions
                    saved_transcriptions = st.session_state.get("transcriptions", {})
                    saved_inserted_transcriptions = st.session_state.get("inserted_transcriptions", set())
                    
                    # Parse and process the SRT file
                    st.session_state["subtitles"] = parse_srt(srt_file)
                    fps = st.session_state.video.get(cv2.CAP_PROP_FPS)
                    if fps > 0:
                        st.session_state["frame_subtitle_map"] = {
                            int(start_time * fps): text
                            for start_time, text in st.session_state["subtitles"].items()
                        }
                    else:
                        st.warning("Could not get FPS from video. Subtitle mapping might be incorrect.")
                    
                    # Restore saved transcriptions and inserted_transcriptions
                    st.session_state["transcriptions"] = saved_transcriptions
                    st.session_state["inserted_transcriptions"] = saved_inserted_transcriptions
                    
                    st.success("SRT file processed! Visual and audio transcripts will be displayed together.")
                    
                except Exception as e:
                    st.error(f"Error processing SRT file: {e}")
            else:
                st.success('SRT file upload detected! File will be processed when you apply settings.')
    else:
        st.success("✅ Audio transcript loaded")
        if st.button("Clear Audio Transcript"):
            st.session_state.audio_transcript = []
            st.experimental_rerun()
    
    st.markdown("---")
    
    # Video and Subtitle Upload
    st.subheader("Video Upload")
    # Video uploader
    if not st.session_state.uploaded:
        uploaded_file = st.file_uploader('Drag and drop a video file', type=['mp4', 'avi', 'mov'], key='video_uploader')
        if uploaded_file is not None:
            st.session_state.pending_video_file = uploaded_file
            st.success('Video upload detected! Video will be processed when you apply settings.')
    else:
        st.success(f"✅ Video loaded ({st.session_state.total_frames} frames)")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Video"):
                if st.session_state.video is not None:
                    st.session_state.video.release()
                st.session_state.video = None
                st.session_state.uploaded = False
                st.session_state.saved_frames = {}
                st.session_state.frame_number = 0
                st.session_state.total_frames = 0
                st.session_state.pending_video_file = None
                st.session_state.subtitles = {}
                # Keep transcriptions in case user wants to reuse them
                # st.session_state.transcriptions = {}
                # st.session_state.inserted_transcriptions = set()
                st.experimental_rerun()
        
        with col2:
            if st.button("Clear Video & Transcriptions"):
                if st.session_state.video is not None:
                    st.session_state.video.release()
                st.session_state.video = None
                st.session_state.uploaded = False
                st.session_state.saved_frames = {}
                st.session_state.frame_number = 0
                st.session_state.total_frames = 0
                st.session_state.pending_video_file = None
                st.session_state.subtitles = {}
                # Clear all transcriptions
                st.session_state.transcriptions = {}
                st.session_state.inserted_transcriptions = set()
                st.experimental_rerun()
    
    st.markdown("---")
    # Create a 3-column layout with empty space on the left to push button to right
    _, _, right_col = st.columns([3, 2, 2])
    with right_col:
        # Only show Process Media button if a video is uploaded and pending processing
        if st.session_state.pending_video_file is not None:
            if st.button("Process Media", key="process_media_button", type="primary"):
                # Process the pending video file if it exists
                try:
                    if not st.session_state.uploaded:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                            temp_file.write(st.session_state.pending_video_file.read())
                            temp_file_path = temp_file.name
                        st.write(f'Video saved temporarily.')
                        if not os.path.exists(temp_file_path):
                            st.error('Temporary file was not created successfully.')
                            st.session_state.uploaded = False
                            st.session_state.video = None
                        else:
                            # Clear previous state before loading new video
                            st.session_state.saved_frames = {}
                            st.session_state.frame_number = 0 # Reset frame number
                            if st.session_state.video is not None:
                                try:
                                    st.session_state.video.release()
                                except Exception as release_error:
                                    st.warning(f"Error releasing previous video: {release_error}")

                            try:
                                st.session_state.video = cv2.VideoCapture(temp_file_path)
                                if st.session_state.video.isOpened():
                                    st.session_state.total_frames = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_COUNT))
                                    st.session_state.uploaded = True

                                    # Process SRT file if it exists
                                    srt_file = st.session_state.get('srt_uploader')
                                    # Save current transcriptions and inserted_transcriptions to restore after SRT processing
                                    saved_transcriptions = st.session_state.get("transcriptions", {})
                                    saved_inserted_transcriptions = st.session_state.get("inserted_transcriptions", set())
                                    
                                    st.session_state["subtitles"] = {} # Ensure subtitles dict exists
                                    st.session_state["frame_subtitle_map"] = {} # Ensure map exists
                                    if srt_file is not None:
                                        try:
                                            st.session_state["subtitles"] = parse_srt(srt_file)
                                            fps = st.session_state.video.get(cv2.CAP_PROP_FPS)
                                            if fps > 0:
                                                st.session_state["frame_subtitle_map"] = {
                                                    int(start_time * fps): text
                                                    for start_time, text in st.session_state["subtitles"].items()
                                                }
                                            else:
                                                st.warning("Could not get FPS from video. Subtitle mapping might be incorrect.")
                                        except Exception as e:
                                            st.error(f"Error parsing SRT file: {e}")
                                    
                                    # Restore the saved transcriptions and inserted_transcriptions
                                    st.session_state["transcriptions"] = saved_transcriptions
                                    st.session_state["inserted_transcriptions"] = saved_inserted_transcriptions

                                    st.session_state.pending_video_file = None
                                    st.success(f'Video opened successfully! Total frames: {st.session_state.total_frames}')
                                    # Set the active tab to Visual Transcription
                                    st.session_state.active_tab = 2 # This might not directly switch tabs, rely on rerun and user click
                                    # Store a flag to indicate we should show the workspace tab content
                                    st.session_state.show_workspace = True
                                    # Rerun to reflect changes and attempt tab switch
                                    st.experimental_rerun()
                                else:
                                    st.error('Could not open video file using OpenCV.')
                                    st.session_state.uploaded = False
                                    st.session_state.video = None
                                    try:
                                        os.unlink(temp_file_path)
                                    except OSError as delete_error:
                                        st.warning(f"Could not delete temporary file: {temp_file_path}, error: {delete_error}")
                            except Exception as cv_error:
                                st.error(f"Error initializing video: {cv_error}")
                                st.session_state.uploaded = False
                                st.session_state.video = None
                                try:
                                    os.unlink(temp_file_path)
                                except OSError:
                                    st.warning(f"Could not delete temporary file: {temp_file_path}")
                except Exception as e:
                    st.error(f"Error processing video file: {e}")
                    st.session_state.uploaded = False
                    if hasattr(st.session_state, 'video') and st.session_state.video is not None:
                        try:
                            st.session_state.video.release()
                        except:
                            pass
                        st.session_state.video = None
        else:
            # Display a message when no video is uploaded (removed placeholder image)
            st.info("Please upload a video in the Media Upload tab to begin.")
            
            # Add a button to allow resetting the session state if needed
            if st.session_state.get("uploaded", False) or st.session_state.get("video") is not None:
                if st.button("Reset Video State"):
                    # Clean up video if it exists
                    if "video" in st.session_state and st.session_state.video is not None:
                        try:
                            st.session_state.video.release()
                        except:
                            pass
                    # Reset all video-related state variables
                    st.session_state.video = None
                    st.session_state.uploaded = False
                    st.session_state.frame_number = 0
                    st.experimental_rerun()


# -----------------------------------------------
# TAB 3: VISUAL TRANSCRIPTION WORKSPACE
# -----------------------------------------------
with workspace_tab:
    # --- Display the video frame and controls only if video is uploaded and available ---
    if st.session_state.get("uploaded", False) and st.session_state.get("video") is not None:
        try:
            # --- Get Current Frame ---
            video_obj = st.session_state.video
            if video_obj is None or not video_obj.isOpened():
                st.error("Video object is not available or not opened. Please load your video in the Media Upload tab.")
                st.session_state.uploaded = False  # Reset the uploaded flag to force re-upload
            else:
                # Add prompt selection radio buttons
                st.subheader("Transcription Settings")
                st.write("Select a prompt category for image description when transcribing:")
                
                # Initialize the prompt category in session state if it doesn't exist
                if "prompt_category" not in st.session_state:
                    st.session_state.prompt_category = "general"
                
                # Create radio buttons for prompt categories
                try:
                    prompt_category = st.radio(
                        "Prompt Category",
                        ["General Purpose", "STEM", "Humanities & Social Sciences", "Business"],
                        index=0,  # Default to General
                        key="prompt_radio"
                    )
                    
                    # Update the session state based on selection
                    category_mapping = {
                        "General Purpose": "general",
                        "STEM": "stem",
                        "Humanities & Social Sciences": "humanities",
                        "Business": "business"
                    }
                    
                    # Update prompt category in session state if changed
                    selected_category = category_mapping[prompt_category]
                    if st.session_state.prompt_category != selected_category:
                        st.session_state.prompt_category = selected_category
                        
                        # Get the prompt text directly from session state using the prompt's display name
                        if prompt_category in st.session_state:
                            # Use the prompt text that was already loaded by load_all_system_prompts
                            st.session_state['gpt-4o']["prompt"] = st.session_state[prompt_category]
                            st.success(f"Loaded {prompt_category} prompt")
                        else:
                            # If not found in session state, try to load it from file
                            try:
                                with open(f"database/prompts/{selected_category}.json", "r") as json_file:
                                    prompt_data = json.load(json_file)
                                    st.session_state['gpt-4o']["prompt"] = prompt_data["prompt"].replace(
                                        "%MAX_WORDS%", str(st.session_state["max_words"]))
                                    st.success(f"Loaded {prompt_data['name']} prompt")
                            except Exception as e:
                                st.error(f"Error loading prompt: {e}")
                except Exception as radio_error:
                    st.error(f"Error with prompt selection: {radio_error}")
                    # Fall back to general prompt
                    st.session_state.prompt_category = "general"
                
                # Instead of displaying the full prompt, just show which prompt category is active
                try:
                    st.markdown(f"### Using {prompt_category} prompt")
                except Exception as prompt_display_error:
                    st.warning(f"Error displaying prompt info: {prompt_display_error}")
                    st.markdown(f"### Using selected prompt")
                
                st.markdown("---")  # Add separator
                
                # Get the current frame with error handling
                try:
                    video_obj.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
                    ret, frame_bgr = video_obj.read()  # Keep original frame in BGR
                    
                    if not ret:
                        st.error(f'Could not read frame {st.session_state.frame_number}. The frame may be corrupted or not exist.')
                        # Try to recover by moving to a different frame
                        if st.session_state.frame_number > 0:
                            st.session_state.frame_number -= 1
                            st.experimental_rerun()
                        elif st.session_state.total_frames > 1:
                            st.session_state.frame_number = 1
                            st.experimental_rerun()
                        else:
                            st.warning("Cannot recover video playback. Please try reloading the video.")
                            frame_bgr = None
                except Exception as frame_error:
                    st.error(f"Error reading frame: {frame_error}")
                    frame_bgr = None

                if frame_bgr is not None:
                    # --- Prepare for Canvas ---
                    try:
                        # Make a copy for display conversion to avoid modifying original frame_bgr
                        frame_rgb = cv2.cvtColor(frame_bgr.copy(), cv2.COLOR_BGR2RGB)
                        pil_image_bg = Image.fromarray(frame_rgb)
                    except Exception as convert_error:
                        st.error(f"Error converting frame for display: {convert_error}")
                        # Create a blank image as fallback
                        pil_image_bg = Image.new('RGB', (640, 480), color=(0, 0, 0))

                    # Initialize the crop variable to avoid NameError when checking later
                    current_processed_crop_bgr = None

                    # --- Canvas Mode and Display ---
                    try:
                        use_rect_mode = st.checkbox("Use Rectangular Crop Mode", value=True, key='crop_mode_checkbox')

                        # Define canvas dimensions (use frame dimensions)
                        canvas_height, canvas_width = frame_bgr.shape[:2]
                        # Optional: Limit max display size for very large videos
                        display_width = min(canvas_width, 1080)
                        display_height = int(display_width * (canvas_height / canvas_width))  # Maintain exact aspect ratio
                        
                        st.write(f"Draw a **{'Rectangle' if use_rect_mode else 'Freeform Shape'}** on the image below.")
                    except Exception as ui_error:
                        st.error(f"Error setting up drawing UI: {ui_error}")
                        use_rect_mode = True  # Default to rectangle mode
                        display_width = 640
                        display_height = 480

                    # Use the canvas_key from session state to force redraw when needed
                    current_canvas_key = f"main_canvas_video_{st.session_state.canvas_key}"
                    try:
                        # Resize the image to 10% of its original size
                        reduced_width = int(display_width * 0.1)
                        reduced_height = int(display_height * 0.1)
                        reduced_image = pil_image_bg.resize((reduced_width, reduced_height), Image.LANCZOS)
                        # Scale back up to maintain display dimensions
                        display_image = reduced_image.resize((display_width, display_height), Image.NEAREST)
                        
                        canvas_result = st_canvas(
                            fill_color="rgba(255, 165, 0, 0.3)",
                            stroke_width=st.session_state.get('stroke_slider', 3), # Use stroke width from settings
                            stroke_color=st.session_state.get('stroke_color', '#00FF00'), # Use stroke color from settings
                            background_color="#eee",
                            background_image=display_image, # Use reduced resolution image
                            update_streamlit=True,
                            height=display_height, # Use calculated height to maintain aspect ratio
                            width=display_width,   # Use calculated display size
                            drawing_mode="rect" if use_rect_mode else "freedraw",
                            key=current_canvas_key # Dynamic key that changes to force canvas reset
                        )
                    except Exception as canvas_error:
                        st.error(f"Error rendering canvas: {canvas_error}")
                        canvas_result = None

                    # --- Process Canvas Result (no preview, just processing) ---
                    try:
                        if canvas_result and canvas_result.json_data is not None and canvas_result.json_data.get("objects"):
                            last_object = canvas_result.json_data["objects"][-1]
                            # Scale factor if canvas size was different from original frame size
                            scale_x = canvas_width / display_width
                            scale_y = canvas_height / display_height

                            if use_rect_mode and last_object["type"] == "rect":
                                # Scale coordinates back to original frame dimensions
                                scaled_rect_data = {
                                    'left': last_object['left'] * scale_x,
                                    'top': last_object['top'] * scale_y,
                                    'width': last_object['width'] * scale_x,
                                    'height': last_object['height'] * scale_y,
                                }
                                current_processed_crop_bgr = crop_rectangular(frame_bgr, scaled_rect_data)

                            elif not use_rect_mode and last_object["type"] == "path":
                                # Scale path points back to original frame dimensions
                                original_path_data = []
                                for point_cmd in last_object["path"]:
                                    scaled_cmd = [point_cmd[0]] # Keep command
                                    # Scale coordinate values
                                    for i in range(1, len(point_cmd)):
                                        scaled_cmd.append(point_cmd[i] * (scale_x if i % 2 != 0 else scale_y))
                                    original_path_data.append(scaled_cmd)

                                current_processed_crop_bgr = crop_freeform(frame_bgr, original_path_data)
                    except Exception as crop_error:
                        st.error(f"Error processing crop: {crop_error}")
                        current_processed_crop_bgr = None
                            
                    # --- Frame Navigation ---
                    st.markdown("---")  # Add separator
                    try:
                        fps = video_obj.get(cv2.CAP_PROP_FPS)
                        total_frames = st.session_state.total_frames
                        total_duration = total_frames / fps if fps > 0 else 0
                        
                        # Convert current frame to time
                        current_time = st.session_state.frame_number / fps if fps > 0 else 0
                        
                        # Create time-based slider
                        time_input = st.slider(
                            'Select time (seconds)',
                            0.0,
                            max(0.1, total_duration),
                            current_time,
                            step=1.0,  # Increment by 1 second
                            key='time_slider'
                        )
                        
                        # Convert selected time back to frame number
                        new_frame_number = int(time_input * fps) if fps > 0 else 0
                        
                        # Update frame number only if time selection changes
                        if new_frame_number != st.session_state.frame_number:
                            st.session_state.frame_number = new_frame_number
                            # Clear transient crop when navigating away
                            try:
                                current_processed_crop_bgr = None
                            except:
                                pass
                            # Force rerun to update the display with the new frame
                            st.experimental_rerun()

                        # Display both time and frame information
                        st.write(f"Current Time: {current_time:.2f}s (Frame: {st.session_state.frame_number})")
                    except Exception as time_error:
                        st.error(f"Error with time navigation: {time_error}")
                    
                    # --- Navigation and Save Buttons ---
                    try:
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            if st.button(f'⬅️ Back {st.session_state.frame_increment} Frame{"s" if st.session_state.frame_increment > 1 else ""}'):
                                if st.session_state.frame_number > 0:
                                    # Calculate new frame number with bounds checking
                                    new_frame = st.session_state.frame_number - st.session_state.frame_increment
                                    # Ensure we don't go below 0
                                    st.session_state.frame_number = max(0, new_frame)
                                    # Clear transient crop when navigating away
                                    try:
                                        current_processed_crop_bgr = None
                                    except:
                                        pass
                                    st.experimental_rerun()

                        with col2:
                            # Save Button
                            if st.button('💾 Save Frame (Crop if Drawn)'):
                                try:
                                    # Re-get the frame to ensure it's the one displayed
                                    video_obj = st.session_state.video
                                    if video_obj and video_obj.isOpened():
                                        try:
                                            video_obj.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
                                            ret_save, frame_bgr_save = video_obj.read()
                                        except Exception as read_error:
                                            st.error(f"Error reading frame for save: {read_error}")
                                            ret_save = False

                                        if ret_save:
                                            saved_image_data_rgb = None
                                            is_cropped_flag = False

                                            # Check if there's a crop to use
                                            if current_processed_crop_bgr is not None and current_processed_crop_bgr.size > 0:
                                                try:
                                                    # Save the cropped version (convert to RGB)
                                                    saved_image_data_rgb = cv2.cvtColor(current_processed_crop_bgr, cv2.COLOR_BGR2RGB)
                                                    is_cropped_flag = True
                                                    st.success(f"Saving **cropped** frame {st.session_state.frame_number}")
                                                except Exception as convert_error:
                                                    st.error(f"Error converting cropped image: {convert_error}")
                                                    # Fallback to full frame
                                                    saved_image_data_rgb = cv2.cvtColor(frame_bgr_save, cv2.COLOR_BGR2RGB)
                                                    is_cropped_flag = False
                                            else:
                                                # Save the full frame version (convert to RGB)
                                                saved_image_data_rgb = cv2.cvtColor(frame_bgr_save, cv2.COLOR_BGR2RGB)
                                                is_cropped_flag = False
                                                st.success(f"Saving **full** frame {st.session_state.frame_number}")

                                            # Store in session state with frame info
                                            try:
                                                # Create a copy of the numpy array
                                                frame_copy = saved_image_data_rgb.copy()
                                                
                                                # Store in session state with clear structure
                                                st.session_state.saved_frames[st.session_state.frame_number] = {
                                                    'frame': frame_copy, # Store RGB numpy array copy
                                                    'frame_number': st.session_state.frame_number,
                                                    'is_cropped': is_cropped_flag,
                                                    'has_visual_transcripts': False,
                                                    'getting_visual_transcripts': False,
                                                    'visual_transcripts': None
                                                }
                                                
                                                # Increment the canvas key to force a redraw/clear of the canvas
                                                st.session_state.canvas_key += 1
                                                
                                                # Clear the crop preview after saving
                                                current_processed_crop_bgr = None
                                                
                                                st.success(f"Saved frame {st.session_state.frame_number}")
                                                st.experimental_rerun()
                                            except Exception as save_error:
                                                st.error(f"Error saving frame: {save_error}")
                                        else:
                                            st.error('Could not capture the frame to save.')
                                    else:
                                        st.error("Video is not available. Please load your video in the Media Upload tab.")
                                except Exception as save_button_error:
                                    st.error(f"Error in save frame process: {save_button_error}")

                        with col3:
                            if st.button(f'➡️ Forward {st.session_state.frame_increment} Frame{"s" if st.session_state.frame_increment > 1 else ""}'):
                                try:
                                    if st.session_state.frame_number < st.session_state.total_frames - 1:
                                        # Calculate new frame number with bounds checking
                                        new_frame = st.session_state.frame_number + st.session_state.frame_increment
                                        # Ensure we don't go beyond the last frame
                                        st.session_state.frame_number = min(st.session_state.total_frames - 1, new_frame)
                                        # Clear transient crop when navigating away
                                        try:
                                            current_processed_crop_bgr = None
                                        except:
                                            pass
                                        st.experimental_rerun()
                                except Exception as forward_error:
                                    st.error(f"Error navigating forward: {forward_error}")
                    except Exception as nav_error:
                        st.error(f"Error with navigation controls: {nav_error}")
                else:
                    st.error(f'Could not read frame {st.session_state.frame_number}. End of video or error.')
                    
                    # Add a button to allow resetting the video
                    if st.button("Reset Video"):
                        try:
                            if "video" in st.session_state:
                                try:
                                    st.session_state.video.release()
                                except:
                                    pass
                            st.session_state.video = None
                            st.session_state.uploaded = False
                            st.experimental_rerun()
                        except Exception as reset_error:
                            st.error(f"Error resetting video: {reset_error}")
        except Exception as e:
            st.error(f"Error accessing or processing video: {e}")
            st.info("Please try uploading your video again in the Media Upload tab.")
            # Reset video-related session state to force clean reload
            st.session_state.uploaded = False
            if "video" in st.session_state:
                try:
                    st.session_state.video.release()
                except:
                    pass
                st.session_state.video = None
    else:
        # Display a message when no video is uploaded (removed placeholder image)
        st.info("Please upload a video in the Media Upload tab to begin.")
        
        # Add a button to allow resetting the session state if needed
        if st.session_state.get("uploaded", False) or st.session_state.get("video") is not None:
            if st.button("Reset Video State"):
                # Clean up video if it exists
                if "video" in st.session_state and st.session_state.video is not None:
                    try:
                        st.session_state.video.release()
                    except:
                        pass
                # Reset all video-related state variables
                st.session_state.video = None
                st.session_state.uploaded = False
                st.session_state.frame_number = 0
                st.experimental_rerun()
    
    # --- Display Final Transcript Information (moved into the workspace tab) ---
    st.markdown("---")
    st.subheader("Combined Transcript (Preview)")
    
    # Use our new merge_transcripts function to get combined chronological transcript
    if st.session_state.audio_transcript:
        st.write(st.session_state.audio_transcript)
    else:
        # Get merged transcripts in chronological order
        try:
            merged_transcripts = merge_transcripts()
        except Exception as e:
            st.error(f"Error merging transcripts: {e}")
            merged_transcripts = []
        
        if merged_transcripts:
            st.write("Showing all transcripts in chronological order:")
            
            # Display merged transcripts
            for entry in merged_transcripts:
                if len(entry) == 3:  # Audio entry (timestamp, text, "audio")
                    timestamp, text, source = entry
                    formatted_time = seconds_to_timestamp(timestamp)
                    st.write(f"**[{formatted_time}]** {text}")
                else:  # Visual entry (timestamp, text, "visual", frame_number)
                    timestamp, text, source, frame_number = entry
                    formatted_time = seconds_to_timestamp(timestamp)
                    st.write(f"**[{formatted_time} - Frame {frame_number}]** 🖼️ *{text}*")
                
            # Add a download option for the combined transcript
            if st.button("Update Combined Transcript Document"):
                # Create a new document with merged transcripts
                doc = Document()
                doc.add_heading("Combined Visual and Audio Transcript", level=1)
                doc.add_paragraph("Timestamps are shown in HH:MM:SS format.")
                for entry in merged_transcripts:
                    if len(entry) == 3:  # Audio entry
                        timestamp, text, source = entry
                        formatted_time = seconds_to_timestamp(timestamp)
                        doc.add_paragraph(f"[{formatted_time}] {text}")
                    else:  # Visual entry
                        timestamp, text, source, frame_number = entry
                        formatted_time = seconds_to_timestamp(timestamp)
                        doc.add_paragraph(f"[{formatted_time} - Frame {frame_number}] {text}")
                
                # Save and offer for download
                temp_doc_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
                doc.save(temp_doc_path)
                with open(temp_doc_path, "rb") as doc_file:
                    st.download_button(
                        "Download Combined Transcript", 
                        doc_file, 
                        file_name="combined_transcript.docx", 
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        else:
            st.info("No transcript data available. Please upload an SRT file in the Media Upload tab or add frame transcriptions.")

# -----------------------------------------------
# Sidebar: Display Saved Frames 
# -----------------------------------------------
with st.sidebar:
    # Add logout button at the top of the sidebar
    if st.button("Logout", key="logout_button"):
        st.session_state.authenticated = False
        st.experimental_rerun()
    
    # Display authentication status
    st.sidebar.success("✅ Authenticated")
    st.sidebar.markdown("---")
        
    st.markdown("### Selected Frames for Transcription")
    
    # Check if saved_frames exists and is not empty
    if not st.session_state.get("saved_frames", {}):
         st.write("No frames selected yet.")
    else:
        # Sort frames for consistent display by frame number
        for frame_number in sorted(st.session_state.saved_frames.keys()):
            frame_info = st.session_state.saved_frames[frame_number]
            
            # Use helper function to get base64
            try:
                 # Re-create base64 string each time to avoid caching issues
                 if 'frame' in frame_info and frame_info['frame'] is not None:
                     base64_img = image_to_base64(frame_info['frame']) # Assumes frame is RGB numpy array
                 else:
                     st.warning(f"Frame {frame_number} data is missing")
                     # Skip this frame to avoid display errors
                     continue
            except Exception as e:
                 st.error(f"Error converting Frame {frame_number} to base64: {e}")
                 # Skip this frame if conversion fails
                 continue

            transcript_text = frame_info.get('visual_transcripts', 'No transcript yet') # Use .get for safety
            is_cropped_text = "(Cropped)" if frame_info.get('is_cropped', False) else "(Full Frame)" # Check crop status

            # Display Card using Markdown with error handling
            try:
                st.markdown(f"""
                    <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                        <h5>Frame {frame_number} {is_cropped_text}</h5>
                        <img src="data:image/jpeg;base64,{base64_img}" style="width:100%;" alt="Frame {frame_number}" />
                        <p style="font-size: smaller; white-space: pre-wrap; word-wrap: break-word;">{transcript_text}</p>
                    </div>
                """, unsafe_allow_html=True)
            except Exception as display_error:
                st.error(f"Error displaying Frame {frame_number}: {display_error}")
                continue

            # Buttons for actions
            col1_side, col2_side = st.columns(2)
            with col1_side:
                # Transcribe Button (only if not already transcribed)
                if not frame_info.get('has_visual_transcripts', False):
                    if st.button(f"Transcribe #{frame_number}", key=f"btn_{frame_number}"):
                        st.info(f"Transcribing Frame {frame_number}...")
                        try:
                            # Pass the saved frame data (numpy array) directly
                            saved_frame_data = frame_info.get('frame')
                            if saved_frame_data is None:
                                st.error(f"Missing frame data for Frame {frame_number}")
                                st.experimental_rerun()
                                continue
                                
                            # Get the image as base64 for OpenAI API
                            try:
                                img_pil = Image.fromarray(saved_frame_data)
                                base64_image = encode_image(img_pil)
                                if not base64_image:
                                    st.error("Failed to encode image")
                                    continue
                            except Exception as img_error:
                                st.error(f"Error processing image: {img_error}")
                                continue
                            
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
                            st.info(f"Using {category_name} prompt: \"{prompt_text}\"")
                            
                            # Show max tokens information
                            max_tokens = int(st.session_state.get("max_words", "20")) * 4
                            st.info(f"Using word limit from configuration: {st.session_state.get('max_words', '20')} tokens")
                            
                            # Ensure API key is available
                            if not GPT_API_KEY:
                                st.error("OpenAI API key not found. Please check your environment variables.")
                                continue
                                
                            # Prepare headers and payload for OpenAI API
                            try:
                                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GPT_API_KEY}"}
                                payload = {
                                    "model": "gpt-4o",
                                    "messages": [
                                        {"role": "user", "content": [
                                            {"type": "text", "text": prompt_text},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                        ]}
                                    ],
                                    "max_tokens": max_tokens
                                }
                            except Exception as payload_error:
                                st.error(f"Error preparing API request: {payload_error}")
                                continue
                            
                            # Make API call with timeout handling
                            try:
                                response = requests.post("https://api.openai.com/v1/chat/completions", 
                                                       headers=headers, 
                                                       json=payload,
                                                       timeout=30)  # 30 second timeout
                                
                                if response.status_code != 200:
                                    st.error(f"API error: {response.status_code} - {response.text}")
                                    continue
                                    
                                gpt_response = response.json()
                                
                                if 'choices' not in gpt_response or len(gpt_response['choices']) == 0:
                                    st.error(f"Unexpected API response format: {gpt_response}")
                                    continue
                                    
                                transcription = gpt_response['choices'][0]['message']['content']
                            except requests.exceptions.Timeout:
                                st.error("API request timed out. Please try again.")
                                continue
                            except requests.exceptions.RequestException as req_err:
                                st.error(f"Request error: {req_err}")
                                continue
                            except Exception as api_error:
                                st.error(f"API error: {api_error}")
                                continue

                            # Update session state
                            try:
                                st.session_state.saved_frames[frame_number]['visual_transcripts'] = transcription
                                st.session_state.saved_frames[frame_number]['has_visual_transcripts'] = True
                                st.session_state["transcriptions"][frame_number] = transcription
                                
                                # Get timestamp if needed
                                if st.session_state.get('video') and st.session_state.get('video').isOpened():
                                    try:
                                        video_obj = st.session_state.video
                                        st.session_state.saved_frames[frame_number]['time_stamp'] = get_frame_timestamp(frame_number, video_obj)
                                    except Exception as ts_error:
                                        st.warning(f"Could not get timestamp for Frame {frame_number}: {ts_error}")
                                        st.session_state.saved_frames[frame_number]['time_stamp'] = "N/A"

                                st.success(f"Transcription completed for Frame {frame_number}.")
                                st.experimental_rerun()  # Update sidebar display
                            except Exception as state_error:
                                st.error(f"Error updating session state: {state_error}")
                        except Exception as api_error:
                            st.error(f"Transcription failed: {api_error}")
                            st.experimental_rerun()

            with col2_side:
                # Insert into Transcript / Remove Button
                if frame_info.get('has_visual_transcripts', False):
                    if st.button(f"Insert to Transcript #{frame_number}", key=f"add_{frame_number}"):
                        try:
                            # When a visual transcript is inserted:
                            # 1. It's added to the existing subtitle text (if matching frame exists)
                            # 2. The frame number is added to inserted_transcriptions set
                            # 3. The merge_transcripts() function will include it in the combined chronological display
                            
                            # Insert into the subtitles dictionary
                            if frame_number in st.session_state.get("frame_subtitle_map", {}):
                                # Get existing subtitle text
                                subtitle_key = None
                                try:
                                    for start_time, text in st.session_state.get("subtitles", {}).items():
                                        try:
                                            if int(start_time * int(st.session_state.video.get(cv2.CAP_PROP_FPS))) == frame_number:
                                                subtitle_key = start_time
                                                break
                                        except (ValueError, TypeError) as key_error:
                                            st.warning(f"Error processing subtitle timestamp {start_time}: {key_error}")
                                            continue
                                except Exception as loop_error:
                                    st.warning(f"Error looping through subtitles: {loop_error}")
                                
                                if subtitle_key is not None:
                                    try:
                                        # Add the GPT transcription to the subtitle
                                        st.session_state["subtitles"][subtitle_key] += f"\n[GPT]: {st.session_state['transcriptions'][frame_number]}"
                                        # Add this frame to the set of inserted transcriptions
                                        st.session_state.inserted_transcriptions.add(frame_number)
                                        st.success(f"Inserted GPT transcription into frame {frame_number} subtitle.")
                                    except Exception as update_error:
                                        st.error(f"Error updating subtitle text: {update_error}")
                                else:
                                    st.warning(f"Could not find subtitle for frame {frame_number}.")
                            else:
                                # Even without a subtitle mapping, we can still track that this frame's 
                                # transcription has been inserted
                                try:
                                    st.session_state.inserted_transcriptions.add(frame_number)
                                    st.warning(f"No subtitle mapping found for frame {frame_number}, but marked as inserted.")
                                except Exception as set_error:
                                    st.error(f"Error updating inserted transcriptions set: {set_error}")
                            
                            # Try to use the insert_VT_into_AT utility if available
                            try:
                                if 'insert_VT_into_AT' in globals() and st.session_state.audio_transcript:
                                    insert_VT_into_AT(frame_info)
                                    st.success(f"Also added Frame {frame_number} info to audio transcript.")
                            except Exception as insert_err:
                                st.warning(f"Could not insert into audio transcript: {insert_err}")
                                
                            st.experimental_rerun()
                        except Exception as insert_err:
                            st.error(f"Error inserting transcription: {insert_err}")
                            # Continue with the rest of the UI, don't crash

                # Add a button to remove a frame from selection
                if st.button(f"Remove #{frame_number}", key=f"del_{frame_number}"):
                    try:
                        if frame_number in st.session_state.saved_frames:
                            # Remove the frame from saved_frames
                            try:
                                del st.session_state.saved_frames[frame_number]
                            except Exception as del_error:
                                st.error(f"Error removing frame from saved_frames: {del_error}")
                            
                            # Remove from inserted_transcriptions if it was inserted
                            try:
                                if frame_number in st.session_state.inserted_transcriptions:
                                    st.session_state.inserted_transcriptions.remove(frame_number)
                            except Exception as set_error:
                                st.warning(f"Error removing frame from inserted_transcriptions: {set_error}")
                            
                            # Remove from transcriptions dictionary
                            try:
                                if frame_number in st.session_state.transcriptions:
                                    del st.session_state.transcriptions[frame_number]
                            except Exception as trans_error:
                                st.warning(f"Error removing frame from transcriptions: {trans_error}")
                                
                            # If this frame has a corresponding subtitle entry, clean up the GPT part
                            try:
                                if frame_number in st.session_state.get("frame_subtitle_map", {}):
                                    # Find the subtitle key
                                    subtitle_key = None
                                    for start_time, text in st.session_state.get("subtitles", {}).items():
                                        try:
                                            if int(start_time * int(st.session_state.video.get(cv2.CAP_PROP_FPS))) == frame_number:
                                                subtitle_key = start_time
                                                break
                                        except Exception as key_error:
                                            continue
                                    
                                    if subtitle_key is not None and "\n[GPT]:" in st.session_state["subtitles"][subtitle_key]:
                                        # Remove only the GPT part
                                        original_text = st.session_state["subtitles"][subtitle_key].split("\n[GPT]:")[0]
                                        st.session_state["subtitles"][subtitle_key] = original_text
                            except Exception as subtitle_error:
                                st.warning(f"Error cleaning up subtitle entry: {subtitle_error}")
                            
                            st.success(f"Removed Frame {frame_number} and its transcription.")
                            st.experimental_rerun()  # Update sidebar
                    except Exception as remove_error:
                        st.error(f"Error during frame removal: {remove_error}")
                        # Don't crash - continue execution

    # Download options
    st.sidebar.subheader("Download Options")
    download_transcript()

# Add spacing at the bottom
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
