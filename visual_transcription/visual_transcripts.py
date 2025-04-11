import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import base64
import requests
import json
import glob
import logging
from logging.handlers import RotatingFileHandler
import sys
from PIL import Image
from openai import OpenAI
from docx import Document
from streamlit_drawable_canvas import st_canvas
from dotenv import load_dotenv
# Import login functionality (split to avoid circular imports)
from login import login_screen, logout, save_user_settings, get_user_settings

# Set up logging
logs_dir = os.path.join("database", "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logger
logger = logging.getLogger("visual_transcripts_logger")
logger.setLevel(logging.INFO)

# Create handlers
log_file = os.path.join(logs_dir, "visual_transcripts.log")
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
console_handler = logging.StreamHandler(sys.stdout)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Visual Transcripts module initialized")

# Set Streamlit theme - Must be the first Streamlit command
st.set_page_config(page_title="VT Generator", page_icon="🖼️", layout="wide")
load_dotenv()

# --- Check for user login before displaying the main app ---
if not login_screen():
    # Stop execution if not logged in or no project selected
    logger.debug("Login check failed - stopping execution")
    st.stop()

# Import additional functionality after login check to avoid circular imports
from login import save_project_data

# --- Main app continues below this point after login and project selection ---
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
        logger.error(f"Error converting image to base64: {e}")
        return None

def get_frame_timestamp(frame_number, video_obj):
    """Get timestamp for a frame."""
    try:
        if video_obj and video_obj.isOpened():
            fps = video_obj.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                seconds = frame_number / fps
                return seconds
        logger.warning(f"Could not get timestamp for frame {frame_number} - using default 0")
        return 0
    except Exception as e:
        logger.error(f"Error getting frame timestamp: {e}")
        return 0

# Function to encode image as base64
def encode_image(image):
    try:
        logger.debug("Encoding image to base64")
        buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        image.save(buffered, format="JPEG")
        with open(buffered.name, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        logger.debug("Image encoded successfully")
        return encoded
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
        return None

# Function to parse SRT files
def parse_srt(file):
    try:
        logger.debug("Parsing SRT file")
        subtitles = {}
        lines = file.read().decode("utf-8").split("\n")
        index, start_time = None, None
        for line in lines:
            line = line.strip()
            if line.isdigit():
                index = int(line)
            elif "-->" in line:
                start_time = line.split(" --> ")[0]
                start_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(start_time.replace(',', '.').split(':'))))
            elif line:
                if index is not None and start_time is not None:
                    subtitles[start_time] = line
        logger.debug(f"Parsed {len(subtitles)} subtitles from SRT file")
        return subtitles
    except Exception as e:
        logger.error(f"Error parsing SRT file: {e}")
        return {}

# --- Cropping Logic Functions ---
def crop_rectangular(image_cv_bgr, rect_data):
    """Crops the OpenCV BGR image using rectangle data."""
    try:
        logger.debug(f"Cropping rectangular area: {rect_data}")
        left = int(rect_data['left'])
        top = int(rect_data['top'])
        width = int(rect_data['width'])
        height = int(rect_data['height'])
        
        if width <= 0 or height <= 0:
            logger.warning("Invalid rectangle dimensions (width or height <= 0)")
            st.warning("Please draw a valid rectangle.")
            return None
            
        h_img, w_img = image_cv_bgr.shape[:2]
        x1, y1 = max(0, left), max(0, top)
        x2, y2 = min(w_img, left + width), min(h_img, top + height)
        
        if x2 <= x1 or y2 <= y1:
            logger.warning(f"Invalid crop area: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
            st.warning("Calculated crop area is outside image bounds or invalid.")
            return None
            
        cropped_bgr = image_cv_bgr[y1:y2, x1:x2]
        logger.debug(f"Successfully cropped rectangular area: {x1},{y1} to {x2},{y2}")
        return cropped_bgr
    except Exception as e:
        logger.error(f"Error cropping rectangular area: {e}")
        return None

def crop_freeform(image_cv_bgr, path_data):
    """Crops the OpenCV BGR image using freeform path data."""
    try:
        logger.debug("Starting freeform crop operation")
        if not path_data:
            logger.warning("Received empty path data for freeform crop")
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
            logger.warning(f"Not enough valid points for freeform crop: {len(points_list)} points (need at least 3)")
            st.warning("Not enough valid points to create a crop area. Please try again.")
            return None
        
        logger.debug(f"Processing freeform crop with {len(points_list)} points")
        
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
                logger.warning("Freeform crop resulted in an empty bounding box")
                st.warning("Freeform crop area resulted in an empty image. Please try a larger selection.")
                return None
                
            # Ensure bounding box is within image boundaries
            x_bb = max(0, x_bb)
            y_bb = max(0, y_bb)
            w_bb = min(w_bb, w_img - x_bb)
            h_bb = min(h_bb, h_img - y_bb)
            
            # Final validation of crop area
            if w_bb <= 0 or h_bb <= 0:
                logger.warning("Final freeform crop area is invalid")
                st.warning("Crop area is outside image boundaries. Please try again.")
                return None
                
            # Extract the bounded region
            cropped_bgr = masked_image_bgr[y_bb:y_bb+h_bb, x_bb:x_bb+w_bb]
            logger.debug(f"Successfully cropped freeform area: {x_bb},{y_bb} to {x_bb+w_bb},{y_bb+h_bb}")
            return cropped_bgr
        
        except Exception as e:
            logger.error(f"Error during freeform crop processing: {e}")
            st.error(f"Error during freeform cropping: {e}")
            return None
    except Exception as e:
        logger.error(f"Error during freeform cropping: {e}")
        st.error(f"Error during freeform cropping: {e}")
        return None

# Function to get list of users from the database directory
def get_settings():
    """Load settings from file if available, otherwise return defaults"""
    logger.debug("Loading settings")
    
    # If user is logged in, get settings from user configuration
    if st.session_state.get("logged_in", False) and st.session_state.get("current_user"):
        username = st.session_state.current_user
        logger.debug(f"Loading settings for logged in user: {username}")
        user_settings = get_user_settings(username)
        
        # Load all settings from user configuration
        if 'frame_increment' in user_settings:
            st.session_state.frame_increment = user_settings['frame_increment']
        if 'stroke_slider' in user_settings:
            st.session_state.stroke_slider = user_settings['stroke_slider']
        if 'stroke_color' in user_settings:
            st.session_state.stroke_color = user_settings['stroke_color']
        if 'max_words' in user_settings:
            st.session_state["max_words"] = user_settings['max_words']
        if 'prompt_category' in user_settings:
            st.session_state.prompt_category = user_settings['prompt_category']
        
        logger.debug(f"Loaded user settings for {username}")
        return
    
    # If not logged in, try to load from default settings file
    settings_path = "visual_transcription/database/default.json"
    try:
        if os.path.exists(settings_path):
            logger.debug(f"Loading default settings from: {settings_path}")
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
            
            # Load additional settings
            if 'max_words' in settings:
                st.session_state["max_words"] = settings['max_words']
            if 'prompt_category' in settings:
                st.session_state.prompt_category = settings['prompt_category']
                
            logger.debug("Loaded default settings successfully")
        else:
            logger.debug(f"Default settings file not found: {settings_path}")
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        # Use defaults if settings can't be loaded

def save_settings():
    """Save current settings to user configuration file or default file"""
    logger.debug("Saving settings")
    
    # If user is logged in, save to user's configuration file
    if st.session_state.get("logged_in", False) and st.session_state.get("current_user"):
        username = st.session_state.current_user
        logger.debug(f"Saving settings for user: {username}")
        
        settings = {
            'frame_increment': st.session_state.get('frame_increment', 1),
            'stroke_slider': st.session_state.get('stroke_slider', 3),
            'stroke_color': st.session_state.get('stroke_color', '#00FF00'),
            'max_words': st.session_state.get('max_words', '100'),
            'prompt_category': st.session_state.get('prompt_category', 'general')
        }
        
        if save_user_settings(username, settings):
            logger.info(f"Settings saved successfully for user: {username}")
            return True
        else:
            # Fall back to default save if user-specific save fails
            logger.warning(f"Could not save to user configuration for {username}. Falling back to default location.")
            st.warning("Could not save to user configuration. Saving to default location instead.")
    
    # If not logged in or user-specific save failed, save to default location
    # Create the directory if it doesn't exist
    os.makedirs("visual_transcription/database", exist_ok=True)
    
    settings_path = "visual_transcription/database/default.json"
    try:
        # Create a settings dictionary with just navigation and drawing settings
        settings = {
            'frame_increment': st.session_state.get('frame_increment', 1),
            'stroke_slider': st.session_state.get('stroke_slider', 3),
            'stroke_color': st.session_state.get('stroke_color', '#00FF00'),
            'max_words': st.session_state.get('max_words', '100'),
            'prompt_category': st.session_state.get('prompt_category', 'general')
        }
        
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        logger.info(f"Settings saved to default location: {settings_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving settings to default location: {e}")
        st.error(f"Error saving settings: {e}")
        return False

# Download full transcript
def download_transcript():
    logger.debug("Preparing transcript for download")
    doc = Document()
    doc.add_heading("Visual Transcript", level=1)
    
    # Use the merged transcripts for a more comprehensive document
    merged_transcripts = merge_transcripts()
    
    if merged_transcripts:
        logger.debug(f"Using {len(merged_transcripts)} merged transcript entries")
        # Add a section explaining the format
        doc.add_paragraph("This document contains both audio transcripts and visual descriptions in chronological order.")
        doc.add_paragraph("Timestamps are shown in seconds from the start of the video.")
        
        # Add all merged transcripts in chronological order
        entries_added = 0
        for entry in merged_transcripts:
            if len(entry) == 3:  # Audio entry (timestamp, text, "audio")
                timestamp, text, source = entry
                para = doc.add_paragraph()
                para.add_run(f"[{timestamp:.2f}s] ").bold = True
                para.add_run(f"{text}")
                entries_added += 1
            else:  # Visual entry (timestamp, text, "visual", frame_number)
                timestamp, text, source, frame_number = entry
                para = doc.add_paragraph()
                para.add_run(f"[{timestamp:.2f}s - Frame {frame_number}] ").bold = True
                para.add_run(f"Visual Description: {text}").italic = True
                entries_added += 1
        logger.debug(f"Added {entries_added} entries to transcript document")
    else:
        # Fall back to original subtitles if no merged transcripts
        logger.debug("No merged transcripts available, using subtitles only")
        entries_added = 0
        for timestamp, text in st.session_state["subtitles"].items():
            doc.add_paragraph(f"{timestamp}: {text}")
            entries_added += 1
        logger.debug(f"Added {entries_added} subtitle entries to transcript document")
    
    try:
        temp_doc_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
        doc.save(temp_doc_path)
        logger.debug(f"Saved transcript document to temporary file: {temp_doc_path}")
        
        with open(temp_doc_path, "rb") as doc_file:
            st.sidebar.download_button("Download Transcript", doc_file, file_name="visual_transcript.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        logger.info("Transcript ready for download")
    except Exception as e:
        logger.error(f"Error preparing transcript for download: {e}")

# Function to merge audio and visual transcripts chronologically
def merge_transcripts():
    """
    Creates a chronologically ordered combined transcript from both 
    audio subtitles and visual frame transcriptions.
    Returns a list of (timestamp, text, source_type) tuples sorted by timestamp.
    """
    logger.debug("Merging audio and visual transcripts")
    combined_entries = []
    
    # Add entries from audio transcripts (subtitles)
    if st.session_state["subtitles"]:
        audio_entries_added = 0
        for timestamp, text in st.session_state["subtitles"].items():
            # Handle potential format issues
            try:
                combined_entries.append((float(timestamp), text, "audio"))
                audio_entries_added += 1
            except (ValueError, TypeError):
                # If timestamp can't be converted to float, use a default
                logger.warning(f"Invalid timestamp format: {timestamp}. Using 0.0 instead.")
                combined_entries.append((0.0, text, "audio"))
                audio_entries_added += 1
        logger.debug(f"Added {audio_entries_added} audio transcript entries")
    
    # Add entries from visual transcriptions
    if st.session_state.get("transcriptions") and st.session_state.get("inserted_transcriptions"):
        visual_entries_added = 0
        # Get video object for timestamp conversion
        video_obj = st.session_state.get('video')
        if video_obj and video_obj.isOpened():
            for frame_number in st.session_state.inserted_transcriptions:
                if frame_number in st.session_state["transcriptions"]:
                    # Convert frame number to timestamp
                    timestamp = get_frame_timestamp(frame_number, video_obj)
                    transcription = st.session_state["transcriptions"][frame_number]
                    combined_entries.append((timestamp, transcription, "visual", frame_number))
                    visual_entries_added += 1
            logger.debug(f"Added {visual_entries_added} visual transcript entries with frame timestamps")
        else:
            # If video isn't available, use placeholder timestamps
            logger.warning("Video object not available for timestamp conversion, using approximate timestamps")
            for frame_number in st.session_state.inserted_transcriptions:
                if frame_number in st.session_state["transcriptions"]:
                    # Use frame number as approximate timestamp
                    transcription = st.session_state["transcriptions"][frame_number]
                    combined_entries.append((float(frame_number)/30.0, transcription, "visual", frame_number))
                    visual_entries_added += 1
            logger.debug(f"Added {visual_entries_added} visual transcript entries with approximate timestamps")
    
    # Sort by timestamp (first element of each tuple)
    result = sorted(combined_entries, key=lambda x: x[0])
    logger.debug(f"Merged transcript contains {len(result)} total entries")
    return result

# Initialize session state variables
# Original session state variables
st.session_state.setdefault("saved_frames", {})
st.session_state.setdefault("saved_subtitles", [])
st.session_state.setdefault("frame_index", 0)
st.session_state.setdefault("frame_subtitle_map", {})
st.session_state.setdefault("subtitles", {})
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
st.session_state["max_words"] = st.session_state.get("max_words", "20")
# Try to load settings
get_settings()

# GPT-4o settings
if "gpt-4o" not in st.session_state:
    try:
        # First try to load default (general) prompt from new prompt system
        prompt_file_path = "database/prompts/general.json"
        if os.path.exists(prompt_file_path):
            with open(prompt_file_path, "r") as json_file:
                gpt4o_data = json.load(json_file)
                st.session_state['gpt-4o'] = {
                    "prompt": gpt4o_data["prompt"], 
                    "max_words": st.session_state["max_words"]
                }
                # Initial replacement
                st.session_state['gpt-4o']["prompt"] = st.session_state['gpt-4o']["prompt"].replace(
                    "%MAX_WORDS%", str(st.session_state["max_words"]))
        # Fall back to legacy path for backward compatibility
        elif os.path.exists(r"utils\chat_GPT.json"):
            with open(r"utils\chat_GPT.json", "r") as json_file:
                gpt4o_data = json.load(json_file)
                st.session_state['gpt-4o'] = {
                    "prompt": gpt4o_data["prompt"], 
                    "max_words": st.session_state["max_words"]
                }
                # Initial replacement
                st.session_state['gpt-4o']["prompt"] = st.session_state['gpt-4o']["prompt"].replace(
                    "%MAX_WORDS%", str(st.session_state["max_words"]))
        else:
            # Default fallback if no files found
            st.session_state['gpt-4o'] = {"prompt": "Describe the image in detail.", "max_words": "100"}
        
        # Initialize prompt category
        st.session_state.prompt_category = "general"
            
    except Exception as e:
        st.error(f"Error loading prompt settings: {e}")
        st.session_state['gpt-4o'] = {"prompt": "Describe the image in detail.", "max_words": "100"}

# Sidebar setup
st.sidebar.title("Saved Frames & Transcripts")

# Display current user and project in sidebar
if st.session_state.get("logged_in", False) and st.session_state.get("current_user"):
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.current_user}")
    
    # Display current project information
    if st.session_state.get("current_project"):
        st.sidebar.markdown("---")
        
        # Use type checking for current project in sidebar
        try:
            current_project = st.session_state.current_project
            if isinstance(current_project, dict) and 'name' in current_project:
                project_name = current_project['name']
                created_date = current_project.get('created_date', 'Unknown date')
                st.sidebar.markdown(f"**Current Project:** {project_name}")
                st.sidebar.markdown(f"**Created:** {created_date}")
                logger.debug(f"Sidebar displaying project as dictionary: {project_name}")
            else:
                # If it's a string or other type
                project_name = str(current_project)
                st.sidebar.markdown(f"**Current Project:** {project_name}")
                logger.debug(f"Sidebar displaying project as string: {project_name}")
        except Exception as e:
            logger.error(f"Error displaying project in sidebar: {e}")
            st.sidebar.markdown("**Project:** Error loading project information")
    
    # Add Save Project button
    st.sidebar.markdown("---")
    save_col, logout_col = st.sidebar.columns(2)
    
    with save_col:
        if st.sidebar.button("Save Project", key="save_project_btn", type="primary"):
            if st.session_state.get("current_project"):
                with st.spinner("Saving project..."):
                    try:
                        current_project = st.session_state.current_project
                        # Get the project name based on type
                        if isinstance(current_project, dict) and 'name' in current_project:
                            project_name = current_project['name']
                        else:
                            project_name = str(current_project)
                        
                        logger.info(f"Saving project: {project_name}")
                        success, message = save_project_data(
                            st.session_state.current_user, 
                            project_name
                        )
                        if success:
                            logger.info(f"Project {project_name} saved successfully")
                            st.sidebar.success("Project saved successfully!")
                        else:
                            logger.error(f"Error saving project {project_name}: {message}")
                            st.sidebar.error(f"Error saving project: {message}")
                    except Exception as e:
                        logger.error(f"Exception during project save: {e}")
                        st.sidebar.error(f"Error saving project: {e}")
            else:
                logger.warning("Attempted to save with no active project")
                st.sidebar.error("No active project to save")
    
    with logout_col:
        if st.sidebar.button("Logout", key="sidebar_logout_btn", type="primary"):
            # Auto-save before logout
            if st.session_state.get("current_project"):
                with st.spinner("Saving before logout..."):
                    try:
                        current_project = st.session_state.current_project
                        # Get the project name based on type
                        if isinstance(current_project, dict) and 'name' in current_project:
                            project_name = current_project['name']
                        else:
                            project_name = str(current_project)
                        
                        logger.info(f"Auto-saving project before logout: {project_name}")
                        save_project_data(
                            st.session_state.current_user, 
                            project_name
                        )
                    except Exception as e:
                        logger.error(f"Error auto-saving project during logout: {e}")
                        # Continue with logout even if save fails
            logout()

# The sidebar content will be updated later in the file

# --- App Title and Initial Setup ---
st.title('Video Transcription Service with Cropping')

# Display project info with proper type checking
try:
    if st.session_state.get("current_project"):
        current_project = st.session_state.current_project
        # Check if current_project is a dictionary or string
        if isinstance(current_project, dict) and 'name' in current_project:
            project_name = current_project['name']
            logger.debug(f"Current project is a dictionary with name: {project_name}")
        else:
            # If it's a string or any other type, convert to string
            project_name = str(current_project)
            logger.debug(f"Current project is not a dictionary, using as string: {project_name}")
        
        st.markdown(f"**Project:** {project_name}")
    else:
        logger.warning("No current project found in session state")
        st.markdown("**Project:** No project selected")
except Exception as e:
    logger.error(f"Error displaying project information: {e}")
    st.markdown("**Project:** Error loading project information")

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
    
    st.markdown("---")
    
    # Drawing Settings
    st.subheader("Drawing Settings")
    # Add drawing settings
    # Add stroke width slider
    stroke_width = st.slider("Stroke width:", 1, 25, st.session_state.stroke_slider, key='stroke_width_input')
    if stroke_width != st.session_state.stroke_slider:
        st.session_state.stroke_slider = stroke_width
        
    # Add color picker for stroke color
    stroke_color = st.color_picker("Stroke color:", st.session_state.stroke_color, key='stroke_color_input')
    if stroke_color != st.session_state.stroke_color:
        st.session_state.stroke_color = stroke_color
    
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
    st.header("Media Upload")
    
    # Audio Transcript
    st.subheader("Audio Transcript")
    
    # Check if we already have SRT data loaded from a project file
    srt_already_loaded = st.session_state.get('srt_file_loaded', False) and st.session_state.get('srt_data') is not None
    
    if srt_already_loaded:
        st.success("✅ SRT file loaded from project")
        
        # Show option to view SRT content
        if st.button("Show SRT Content", key="show_srt_content"):
            srt_data = st.session_state.get('srt_data', '')
            # Show only first 20 lines to avoid overwhelming the UI
            preview_lines = srt_data.split('\n')[:20]
            st.code('\n'.join(preview_lines) + ('\n...' if len(srt_data.split('\n')) > 20 else ''), language='text')
            
    else:
        # Replace the old uploader with the SRT file uploader
        srt_file = st.file_uploader("Upload Subtitle File (SRT)", type=["srt"], key='srt_uploader')
        if srt_file is not None:
            # Store the SRT content in session state for saving later
            try:
                srt_content = srt_file.read()
                st.session_state.srt_data = srt_content.decode('utf-8')
                # Reset the file pointer for later use
                srt_file.seek(0)
                logger.debug("Stored SRT data in session state for saving")
            except Exception as e:
                logger.error(f"Error storing SRT data: {e}")
                
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
            # Only show this if no file is uploaded and no SRT data is loaded
            st.info("Please upload an SRT file for audio transcription")
    
    # Option to clear audio transcript
    if st.button("Clear Audio Transcript"):
        st.session_state.audio_transcript = []
        # Clear SRT data as well
        if 'srt_data' in st.session_state:
            del st.session_state.srt_data
        if 'srt_uploader' in st.session_state:
            del st.session_state.srt_uploader
        if 'srt_file_loaded' in st.session_state:
            del st.session_state.srt_file_loaded
        if 'subtitles' in st.session_state:
            st.session_state.subtitles = {}
        st.success("Audio transcript cleared.")
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
                if not st.session_state.uploaded:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                        temp_file.write(st.session_state.pending_video_file.read())
                        temp_file_path = temp_file.name
                    
                    logger.info(f"Video file saved to temporary location: {temp_file_path}")
                    st.write(f'Video saved temporarily.')
                    
                    if not os.path.exists(temp_file_path):
                        logger.error(f"Temporary file was not created successfully: {temp_file_path}")
                        st.error('Temporary file was not created successfully.')
                        st.session_state.uploaded = False
                        st.session_state.video = None
                    else:
                        # Clear previous state before loading new video
                        st.session_state.saved_frames = {}
                        st.session_state.frame_number = 0 # Reset frame number
                        if st.session_state.video is not None:
                            logger.debug("Releasing previous video object")
                            st.session_state.video.release()

                        logger.info("Opening video with OpenCV")
                        st.session_state.video = cv2.VideoCapture(temp_file_path)
                        if st.session_state.video.isOpened():
                            total_frames = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = st.session_state.video.get(cv2.CAP_PROP_FPS)
                            width = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            
                            logger.info(f"Video opened successfully: {width}x{height}, {fps} fps, {total_frames} frames")
                            st.session_state.total_frames = total_frames
                            st.session_state.uploaded = True

                            # Process SRT file if it exists
                            srt_file = st.session_state.get('srt_uploader')
                            # Check if we have SRT data from a loaded file instead of a file uploader
                            has_loaded_srt = st.session_state.get('srt_file_loaded', False) and st.session_state.get('srt_data') is not None
                            
                            # Save current transcriptions and inserted_transcriptions to restore after SRT processing
                            saved_transcriptions = st.session_state.get("transcriptions", {})
                            saved_inserted_transcriptions = st.session_state.get("inserted_transcriptions", set())
                            
                            st.session_state["subtitles"] = {} # Ensure subtitles dict exists
                            st.session_state["frame_subtitle_map"] = {} # Ensure map exists
                            
                            if srt_file is not None:
                                try:
                                    logger.info("Processing SRT file from uploader")
                                    st.session_state["subtitles"] = parse_srt(srt_file)
                                    
                                    if fps > 0:
                                        # Map subtitles to frame numbers
                                        frame_subtitle_count = 0
                                        st.session_state["frame_subtitle_map"] = {}
                                        
                                        for start_time, text in st.session_state["subtitles"].items():
                                            frame_num = int(float(start_time) * fps)
                                            st.session_state["frame_subtitle_map"][frame_num] = text
                                            frame_subtitle_count += 1
                                            
                                        logger.info(f"Mapped {frame_subtitle_count} subtitles to frames")
                                    else:
                                        logger.warning("Could not get FPS from video. Subtitle mapping might be incorrect.")
                                        st.warning("Could not get FPS from video. Subtitle mapping might be incorrect.")
                                except Exception as e:
                                    logger.error(f"Error parsing SRT file: {e}", exc_info=True)
                                    st.error(f"Error parsing SRT file: {e}")
                            elif has_loaded_srt:
                                # We have SRT data loaded from a file
                                try:
                                    logger.info("Processing SRT data from loaded file")
                                    # We already have parsed subtitles in session state from the file loading process
                                    # Just need to map them to frames
                                    if fps > 0 and st.session_state.get("subtitles"):
                                        # Map subtitles to frame numbers
                                        frame_subtitle_count = 0
                                        st.session_state["frame_subtitle_map"] = {}
                                        
                                        for start_time, text in st.session_state["subtitles"].items():
                                            frame_num = int(float(start_time) * fps)
                                            st.session_state["frame_subtitle_map"][frame_num] = text
                                            frame_subtitle_count += 1
                                            
                                        logger.info(f"Mapped {frame_subtitle_count} subtitles from loaded SRT data to frames")
                                    else:
                                        logger.warning("Could not get FPS from video or subtitles not loaded properly.")
                                        st.warning("Could not get FPS from video or subtitles not loaded properly.")
                                except Exception as e:
                                    logger.error(f"Error processing loaded SRT data: {e}", exc_info=True)
                                    st.error(f"Error processing loaded SRT data: {e}")
                            else:
                                logger.debug("No SRT file or data provided")
                                
                            # Restore the saved transcriptions and inserted_transcriptions
                            st.session_state["transcriptions"] = saved_transcriptions
                            st.session_state["inserted_transcriptions"] = saved_inserted_transcriptions
                            logger.debug(f"Restored {len(saved_transcriptions)} transcriptions and {len(saved_inserted_transcriptions)} inserted transcriptions")

                            st.session_state.pending_video_file = None
                            st.success(f'Video opened successfully! Total frames: {st.session_state.total_frames}')
                            # Set the active tab to Visual Transcription
                            st.session_state.active_tab = 2 # This might not directly switch tabs, rely on rerun and user click
                            # Store a flag to indicate we should show the workspace tab content
                            st.session_state.show_workspace = True
                            logger.info("Setting flag to show workspace tab")
                            # Rerun to reflect changes and attempt tab switch
                            st.experimental_rerun()
                        else:
                            logger.error("Could not open video file using OpenCV")
                            st.error('Could not open video file using OpenCV.')
                            st.session_state.uploaded = False
                            st.session_state.video = None
                            try:
                                os.unlink(temp_file_path)
                                logger.debug(f"Deleted temporary file: {temp_file_path}")
                            except OSError as e:
                                logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")
                                st.warning(f"Could not delete temporary file: {temp_file_path}")


        else:
            # Display a disabled button or message when no video is uploaded
             st.write("Please upload a video before processing.") # Changed from button to text

# -----------------------------------------------
# TAB 3: VISUAL TRANSCRIPTION WORKSPACE
# -----------------------------------------------
with workspace_tab:
    # --- Display the video frame and controls only if video is uploaded and available ---
    if st.session_state.get("uploaded", False) and st.session_state.get("video") is not None:
        try:
            # --- Get Current Frame ---
            video_obj = st.session_state.video

            st.success(f"Video object: {video_obj.isOpened()}")
            
            
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
                    # Load the appropriate prompt from the JSON file
                    try:
                        with open(f"database/prompts/{selected_category}.json", "r") as json_file:
                            prompt_data = json.load(json_file)
                            st.session_state['gpt-4o'] = {
                                "prompt": prompt_data["prompt"], 
                                "max_words": st.session_state["max_words"]
                            }
                            # Replace placeholder with actual max words
                            st.session_state['gpt-4o']["prompt"] = st.session_state['gpt-4o']["prompt"].replace(
                                "%MAX_WORDS%", str(st.session_state["max_words"]))
                            st.success(f"Loaded {prompt_data['name']} prompt")
                    except Exception as e:
                        st.error(f"Error loading prompt: {e}")
                
                # Display current prompt
                current_prompt = st.session_state['gpt-4o'].get("prompt", "No prompt available")
                st.markdown(f"### Current Prompt")
                st.text_area(
                    "Current prompt (resizable)",
                    value=current_prompt,
                    height=100,
                    key="prompt_display_area",
                    disabled=True,
                    label_visibility="collapsed"
                )
                
                st.markdown("---")  # Add separator
                
                video_obj.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
                ret, frame_bgr = video_obj.read()  # Keep original frame in BGR

                if ret:
                    # --- Prepare for Canvas ---
                    # Make a copy for display conversion to avoid modifying original frame_bgr
                    frame_rgb = cv2.cvtColor(frame_bgr.copy(), cv2.COLOR_BGR2RGB)
                    pil_image_bg = Image.fromarray(frame_rgb)

                    # Initialize the crop variable to avoid NameError when checking later
                    current_processed_crop_bgr = None

                    # --- Canvas Mode and Display ---
                    use_rect_mode = st.checkbox("Use Rectangular Crop Mode", value=True, key='crop_mode_checkbox')

                    # Define canvas dimensions (use frame dimensions)
                    canvas_height, canvas_width = frame_bgr.shape[:2]
                    # Optional: Limit max display size for very large videos
                    display_width = min(canvas_width, 1080)
                    display_height = int(display_width * (canvas_height / canvas_width))  # Maintain exact aspect ratio
                    
                    st.write(f"Draw a **{'Rectangle' if use_rect_mode else 'Freeform Shape'}** on the image below.")

                    # Increase the canvas key from session state to force redraw when needed
                    current_canvas_key = f"main_canvas_video_{st.session_state.canvas_key}"
                    logger.debug(f"Rendering canvas with key: {current_canvas_key}")
                    try:
                        canvas_result = st_canvas(
                            fill_color="rgba(255, 165, 0, 0.3)",
                            stroke_width=st.session_state.get('stroke_slider', 3), # Use stroke width from settings
                            stroke_color=st.session_state.get('stroke_color', '#00FF00'), # Use stroke color from settings
                            background_color="#eee",
                            background_image=pil_image_bg, # Use PIL image here
                            update_streamlit=True,
                            height=display_height, # Use calculated height to maintain aspect ratio
                            width=display_width,   # Use calculated display size
                            drawing_mode="rect" if use_rect_mode else "freedraw",
                            key=current_canvas_key # Dynamic key that changes to force canvas reset
                        )
                        logger.debug(f"Canvas rendered successfully, mode: {'rect' if use_rect_mode else 'freedraw'}")
                    except Exception as canvas_error:
                        logger.error(f"Error rendering canvas: {canvas_error}", exc_info=True)
                        st.error(f"Error rendering canvas: {canvas_error}")
                        canvas_result = None

                    # Process canvas result
                    if canvas_result and canvas_result.json_data is not None and canvas_result.json_data.get("objects"):
                        last_object = canvas_result.json_data["objects"][-1]
                        logger.debug(f"Processing canvas object type: {last_object.get('type')}")
                        
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
                            logger.debug(f"Scaling rectangle: {scaled_rect_data}")
                            current_processed_crop_bgr = crop_rectangular(frame_bgr, scaled_rect_data)
                            if current_processed_crop_bgr is not None:
                                logger.info(f"Successfully cropped rectangular region: {current_processed_crop_bgr.shape}")

                        elif not use_rect_mode and last_object["type"] == "path":
                            # Scale path points back to original frame dimensions
                            original_path_data = []
                            for point_cmd in last_object["path"]:
                                scaled_cmd = [point_cmd[0]] # Keep command
                                # Scale coordinate values
                                for i in range(1, len(point_cmd)):
                                    scaled_cmd.append(point_cmd[i] * (scale_x if i % 2 != 0 else scale_y))
                                original_path_data.append(scaled_cmd)
                            
                            logger.debug(f"Scaling freeform path with {len(original_path_data)} points")
                            current_processed_crop_bgr = crop_freeform(frame_bgr, original_path_data)
                            if current_processed_crop_bgr is not None:
                                logger.info(f"Successfully cropped freeform region: {current_processed_crop_bgr.shape}")
                    else:
                        if canvas_result and canvas_result.json_data is not None:
                            logger.debug("Canvas has no objects to process")
                            
                    # --- Frame Navigation ---
                    st.markdown("---")  # Add separator
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
                    
                    # --- Navigation and Save Buttons ---
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
                            logger.info(f"User requested to save frame {st.session_state.frame_number}")
                            # Re-get the frame to ensure it's the one displayed
                            video_obj = st.session_state.video
                            if video_obj and video_obj.isOpened():
                                video_obj.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
                                ret_save, frame_bgr_save = video_obj.read()

                                if ret_save:
                                    saved_image_data_rgb = None
                                    is_cropped_flag = False

                                    # Check if there's a crop to use
                                    if current_processed_crop_bgr is not None and current_processed_crop_bgr.size > 0:
                                        # Save the cropped version (convert to RGB)
                                        saved_image_data_rgb = cv2.cvtColor(current_processed_crop_bgr, cv2.COLOR_BGR2RGB)
                                        is_cropped_flag = True
                                        logger.info(f"Saving cropped frame {st.session_state.frame_number}, shape: {saved_image_data_rgb.shape}")
                                        st.success(f"Saving **cropped** frame {st.session_state.frame_number}")
                                    else:
                                        # Save the full frame version (convert to RGB)
                                        saved_image_data_rgb = cv2.cvtColor(frame_bgr_save, cv2.COLOR_BGR2RGB)
                                        is_cropped_flag = False
                                        logger.info(f"Saving full frame {st.session_state.frame_number}, shape: {saved_image_data_rgb.shape}")
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
                                        logger.debug(f"Incremented canvas key to {st.session_state.canvas_key} to force canvas reset")
                                        
                                        # Clear the crop preview after saving
                                        current_processed_crop_bgr = None
                                        
                                        logger.info(f"Frame {st.session_state.frame_number} saved successfully")
                                        st.success(f"Saved frame {st.session_state.frame_number}")
                                        st.experimental_rerun()
                                    except Exception as save_error:
                                        logger.error(f"Error saving frame {st.session_state.frame_number}: {save_error}", exc_info=True)
                                        st.error(f"Error saving frame: {save_error}")
                                else:
                                    logger.error(f"Could not capture frame {st.session_state.frame_number} for saving")
                                    st.error('Could not capture the frame to save.')
                            else:
                                logger.error("Video is not available for saving frame")
                                st.error("Video is not available. Please load your video in the Media Upload tab.")

                    with col3:
                        if st.button(f'➡️ Forward {st.session_state.frame_increment} Frame{"s" if st.session_state.frame_increment > 1 else ""}'):
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
                else:
                    st.error(f'Could not read frame {st.session_state.frame_number}. End of video or error.')
                    
                    # Add a button to allow resetting the video
                    if st.button("Reset Video"):
                        if "video" in st.session_state:
                            try:
                                st.session_state.video.release()
                            except:
                                pass
                        st.session_state.video = None
                        st.session_state.uploaded = False
                        st.experimental_rerun()
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
        # Display a placeholder when no video is uploaded
        st.subheader("No Video Loaded")
        
        # Try to load and display the placeholder image
        try:
            # Fix the path to the placeholder image - use forward slashes and remove leading slash
            placeholder_image_path = "image_place_holder.png"
            if os.path.exists(placeholder_image_path):
                # Load the image with PIL
                placeholder_img = Image.open(placeholder_image_path)
                # Resize to exactly 720x480 pixels
                placeholder_img = placeholder_img.resize((720, 480))
                # Display the resized placeholder image
                st.image(placeholder_img, caption="Please upload a video in the Media Upload tab to begin.")
            else:
                st.warning(f"Placeholder image not found at: {placeholder_image_path}")
                st.info("Please upload a video in the Media Upload tab to begin working with frames.")
        except Exception as e:
            st.error(f"Error displaying placeholder image: {e}")
            st.info("Please upload a video in the Media Upload tab to begin working with frames.")
            
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
        merged_transcripts = merge_transcripts()
        
        if merged_transcripts:
            st.write("Showing all transcripts in chronological order:")
            
            # Display merged transcripts
            for entry in merged_transcripts:
                if len(entry) == 3:  # Audio entry (timestamp, text, "audio")
                    timestamp, text, source = entry
                    st.write(f"**[{timestamp:.2f}s]** {text}")
                else:  # Visual entry (timestamp, text, "visual", frame_number)
                    timestamp, text, source, frame_number = entry
                    st.write(f"**[{timestamp:.2f}s - Frame {frame_number}]** 🖼️ *{text}*")
                
            # Add a download option for the combined transcript
            if st.button("Update Combined Transcript Document"):
                # Create a new document with merged transcripts
                doc = Document()
                doc.add_heading("Combined Visual and Audio Transcript", level=1)
                for entry in merged_transcripts:
                    if len(entry) == 3:  # Audio entry
                        timestamp, text, source = entry
                        doc.add_paragraph(f"[{timestamp:.2f}s] {text}")
                    else:  # Visual entry
                        timestamp, text, source, frame_number = entry
                        doc.add_paragraph(f"[{timestamp:.2f}s - Frame {frame_number}] {text}")
                
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
                        logger.info(f"Initiating transcription for Frame {frame_number}")
                        st.info(f"Transcribing Frame {frame_number}...")
                        try:
                            # Pass the saved frame data (numpy array) directly
                            saved_frame_data = frame_info['frame'] # This is already RGB
                            logger.debug(f"Loaded frame data for transcription, shape: {saved_frame_data.shape if isinstance(saved_frame_data, np.ndarray) else 'PIL Image'}")
                            
                            # Get the image as base64 for OpenAI API
                            img_pil = Image.fromarray(saved_frame_data)
                            base64_image = encode_image(img_pil)
                            if not base64_image:
                                logger.error(f"Failed to encode image for Frame {frame_number}")
                                st.error("Failed to encode image for API request")
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
                            logger.info(f"Using {category_name} prompt category for Frame {frame_number}")
                            st.info(f"Using {category_name} prompt: \"{prompt_text}\"")
                            
                            # Show max tokens information
                            max_tokens = int(st.session_state["max_words"]) * 4
                            logger.debug(f"Setting max tokens to {max_tokens} (words: {st.session_state['max_words']})")
                            st.info(f"Using word limit from configuration: {st.session_state['max_words']} tokens")
                            
                            # Prepare headers and payload for OpenAI API
                            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GPT_API_KEY}"}
                            payload = {
                                "model": "gpt-4o",
                                "messages": [
                                    {"role": "user", "content": [
                                        {"type": "text", "text": prompt_text},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                    ]}
                                ],
                                "max_tokens": int(st.session_state["max_words"]) * 4  # Convert word count to approximate token count (4 tokens per word on average)
                            }
                            
                            # Make API call
                            logger.info(f"Sending request to OpenAI API for Frame {frame_number}")
                            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                            
                            if response.status_code != 200:
                                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                                st.error(f"API request failed: {response.status_code}")
                                continue
                            
                            gpt_response = response.json()
                            logger.debug(f"Received response from OpenAI API for Frame {frame_number}")
                            transcription = gpt_response['choices'][0]['message']['content']
                            logger.info(f"Transcription successful for Frame {frame_number} - {len(transcription)} characters")

                            # Update session state
                            st.session_state.saved_frames[frame_number]['visual_transcripts'] = transcription
                            st.session_state.saved_frames[frame_number]['has_visual_transcripts'] = True
                            st.session_state["transcriptions"][frame_number] = transcription
                            
                            # Get timestamp if needed
                            if st.session_state.get('video') and st.session_state.get('video').isOpened():
                                try:
                                    video_obj = st.session_state.video
                                    timestamp = get_frame_timestamp(frame_number, video_obj)
                                    st.session_state.saved_frames[frame_number]['time_stamp'] = timestamp
                                    logger.debug(f"Added timestamp {timestamp}s to Frame {frame_number}")
                                except Exception as ts_error:
                                    logger.warning(f"Could not get timestamp for Frame {frame_number}: {ts_error}")
                                    st.warning(f"Could not get timestamp for Frame {frame_number}: {ts_error}")
                                    st.session_state.saved_frames[frame_number]['time_stamp'] = "N/A"

                            st.success(f"Transcription completed for Frame {frame_number}.")
                            st.experimental_rerun()  # Update sidebar display
                        except Exception as api_error:
                            logger.error(f"Transcription failed for Frame {frame_number}: {api_error}", exc_info=True)
                            st.error(f"Transcription failed: {api_error}")

            with col2_side:
                # Insert into Transcript / Remove Button
                if frame_info.get('has_visual_transcripts', False):
                    if st.button(f"Insert to Transcript #{frame_number}", key=f"add_{frame_number}"):
                        logger.info(f"User requested to insert Frame {frame_number} transcription into transcript")
                        try:
                            # When a visual transcript is inserted:
                            # 1. It's added to the existing subtitle text (if matching frame exists)
                            # 2. The frame number is added to inserted_transcriptions set
                            # 3. The merge_transcripts() function will include it in the combined chronological display
                            
                            transcript_text = st.session_state['transcriptions'][frame_number]
                            logger.debug(f"Transcript text for Frame {frame_number}: {transcript_text[:50]}...")
                            
                            # Insert into the subtitles dictionary
                            if frame_number in st.session_state["frame_subtitle_map"]:
                                # Get existing subtitle text
                                subtitle_key = None
                                for start_time, text in st.session_state["subtitles"].items():
                                    if int(float(start_time) * int(st.session_state.video.get(cv2.CAP_PROP_FPS))) == frame_number:
                                        subtitle_key = start_time
                                        break
                                
                                if subtitle_key is not None:
                                    # Add the GPT transcription to the subtitle
                                    logger.info(f"Adding GPT transcription to existing subtitle at timestamp {subtitle_key}")
                                    st.session_state["subtitles"][subtitle_key] += f"\n[GPT]: {st.session_state['transcriptions'][frame_number]}"
                                    # Add this frame to the set of inserted transcriptions
                                    st.session_state.inserted_transcriptions.add(frame_number)
                                    st.success(f"Inserted GPT transcription into frame {frame_number} subtitle.")
                                else:
                                    logger.warning(f"Could not find subtitle for frame {frame_number} despite being in frame_subtitle_map")
                                    st.warning(f"Could not find subtitle for frame {frame_number}.")
                            else:
                                # Even without a subtitle mapping, we can still track that this frame's 
                                # transcription has been inserted
                                logger.info(f"No subtitle mapping found for frame {frame_number}, marking as inserted independently")
                                st.session_state.inserted_transcriptions.add(frame_number)
                                st.warning(f"No subtitle mapping found for frame {frame_number}, but marked as inserted.")
                            
                            # Log the current count of inserted transcriptions
                            logger.debug(f"Total inserted transcriptions: {len(st.session_state.inserted_transcriptions)}")
                            
                            # Try to use the insert_VT_into_AT utility if available
                            try:
                                if 'insert_VT_into_AT' in globals() and st.session_state.audio_transcript:
                                    insert_VT_into_AT(frame_info)
                                    logger.info(f"Successfully inserted Frame {frame_number} info into audio transcript")
                                    st.success(f"Also added Frame {frame_number} info to audio transcript.")
                            except Exception as insert_err:
                                logger.error(f"Could not insert into audio transcript: {insert_err}", exc_info=True)
                                st.warning(f"Could not insert into audio transcript: {insert_err}")
                                
                            st.experimental_rerun()
                        except Exception as insert_err:
                            logger.error(f"Error inserting transcription for Frame {frame_number}: {insert_err}", exc_info=True)
                            st.error(f"Error inserting transcription: {insert_err}")

                # Add a button to remove a frame from selection
                if st.button(f"Remove #{frame_number}", key=f"del_{frame_number}"):
                    if frame_number in st.session_state.saved_frames:
                        # Remove the frame from saved_frames
                        del st.session_state.saved_frames[frame_number]
                        
                        # Remove from inserted_transcriptions if it was inserted
                        if frame_number in st.session_state.inserted_transcriptions:
                            st.session_state.inserted_transcriptions.remove(frame_number)
                        
                        # Remove from transcriptions dictionary
                        if frame_number in st.session_state.transcriptions:
                            del st.session_state.transcriptions[frame_number]
                            
                        # If this frame has a corresponding subtitle entry, clean up the GPT part
                        if frame_number in st.session_state["frame_subtitle_map"]:
                            # Find the subtitle key
                            subtitle_key = None
                            for start_time, text in st.session_state["subtitles"].items():
                                if int(start_time * int(st.session_state.video.get(cv2.CAP_PROP_FPS))) == frame_number:
                                    subtitle_key = start_time
                                    break
                            
                            if subtitle_key is not None and "\n[GPT]:" in st.session_state["subtitles"][subtitle_key]:
                                # Remove only the GPT part
                                original_text = st.session_state["subtitles"][subtitle_key].split("\n[GPT]:")[0]
                                st.session_state["subtitles"][subtitle_key] = original_text
                        
                        st.success(f"Removed Frame {frame_number} and its transcription.")
                        st.experimental_rerun()  # Update sidebar

    # Download options
    st.sidebar.subheader("Download Options")
    download_transcript()

# Add spacing at the bottom
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
