import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import base64
import requests
import json
import glob
import re
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
    try:
        # If already authenticated, return True
        if "authenticated" in st.session_state and st.session_state.authenticated:
            return True
        
        # If not set yet, initialize it to False
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        # Create login form
        st.title("VT Generator - Authentication Required")
        st.markdown("### Please enter your password to continue")
        st.markdown("This application requires authentication to access its functionality.")
        
        # Create columns for centered form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            try:
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
            except Exception as input_error:
                st.error(f"Authentication input error: {input_error}")
                return False
        
        # Display application title only (removed placeholder image)
        st.markdown("### VT Generator - Visual Transcription Service")
        
        return False
    except Exception as auth_error:
        st.error(f"Authentication error: {auth_error}")
        # In case of error, ensure we don't let through
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
            try:
                image = Image.fromarray(image)
            except Exception as conversion_error:
                st.error(f"Error converting array to image: {conversion_error}")
                return ""
        
        try:
            buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            image.save(buffered, format="JPEG")
            
            try:
                with open(buffered.name, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
            except Exception as read_error:
                st.error(f"Error reading image file: {read_error}")
                return ""
            finally:
                # Ensure temp file is cleaned up even if there's an error
                try:
                    os.unlink(buffered.name)
                except:
                    pass
        except Exception as save_error:
            st.error(f"Error saving image to temporary file: {save_error}")
            return ""
    except Exception as e:
        st.error(f"Error in image_to_base64: {e}")
        return ""

def get_frame_timestamp(frame_number, video_obj):
    """Get timestamp for a frame."""
    try:
        if video_obj is None:
            return 0
            
        if not isinstance(video_obj, cv2.VideoCapture):
            st.warning("Invalid video object type")
            return 0
            
        if not video_obj.isOpened():
            st.warning("Video object is not open")
            return 0
            
        fps = video_obj.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            st.warning("Invalid FPS value in video")
            return 0
            
        seconds = frame_number / fps
        return seconds
    except Exception as e:
        st.error(f"Error getting frame timestamp: {e}")
        return 0

# Function to encode image as base64
def encode_image(image):
    try:
        if image is None:
            st.error("No image provided for encoding")
            return ""
            
        try:
            buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            
            try:
                image.save(buffered, format="JPEG")
            except Exception as save_error:
                st.error(f"Error saving image: {save_error}")
                return ""
                
            try:
                with open(buffered.name, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode("utf-8")
                    return encoded
            except Exception as read_error:
                st.error(f"Error reading/encoding image: {read_error}")
                return ""
            finally:
                # Clean up temp file
                try:
                    os.unlink(buffered.name)
                except:
                    pass
        except Exception as temp_error:
            st.error(f"Error creating temporary file: {temp_error}")
            return ""
    except Exception as e:
        st.error(f"Error in encode_image: {e}")
        return ""

# Function to convert seconds to HH:MM:SS format
def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    try:
        if seconds is None:
            return "00:00:00"
            
        if not isinstance(seconds, (int, float)):
            seconds = float(seconds)  # Try to convert
            
        if seconds < 0:
            seconds = 0  # Ensure non-negative
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02}:{minutes:02}:{secs:02}"
    except Exception as e:
        st.warning(f"Error converting seconds to timestamp: {e}")
        return "00:00:00"

# Function to parse SRT files
def parse_srt(file):
    try:
        if file is None:
            st.error("No subtitle file provided")
            return {}
            
        subtitles = {}
        
        try:
            file_content = file.read()
            
            try:
                lines = file_content.decode("utf-8").split("\n")
            except UnicodeDecodeError:
                # Try other common encodings if UTF-8 fails
                try:
                    lines = file_content.decode("latin-1").split("\n")
                except Exception:
                    try:
                        lines = file_content.decode("cp1252").split("\n")
                    except Exception as enc_error:
                        st.error(f"Failed to decode subtitle file: {enc_error}")
                        return {}
        except Exception as read_error:
            st.error(f"Error reading subtitle file: {read_error}")
            return {}
        
        index, start_time = None, None
        line_number = 0
        
        for line in lines:
            line_number += 1
            try:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Parse index
                if line.isdigit():
                    index = int(line)
                    continue
                    
                # Parse timestamp
                if "-->" in line:
                    try:
                        time_parts = line.split(" --> ")
                        if len(time_parts) < 2:
                            st.warning(f"Invalid timestamp format at line {line_number}: {line}")
                            continue
                            
                        start_time_str = time_parts[0]
                        
                        # Handle various time formats
                        start_time_str = start_time_str.replace(',', '.')  # Convert comma to decimal point
                        
                        # Extract hours, minutes, seconds
                        time_components = start_time_str.split(':')
                        if len(time_components) != 3:
                            st.warning(f"Invalid time format at line {line_number}: {start_time_str}")
                            continue
                            
                        hours = float(time_components[0])
                        minutes = float(time_components[1])
                        seconds = float(time_components[2])
                        
                        # Calculate total seconds
                        start_time = hours * 3600 + minutes * 60 + seconds
                    except Exception as time_error:
                        st.warning(f"Error parsing timestamp at line {line_number}: {time_error}")
                        start_time = None
                    continue
                    
                # If we have both index and start_time, this line is subtitle text
                if index is not None and start_time is not None:
                    # Add or append to subtitle text
                    if start_time in subtitles:
                        subtitles[start_time] += " " + line
                    else:
                        subtitles[start_time] = line
                    continue
                    
            except Exception as line_error:
                st.warning(f"Error parsing line {line_number}: {line_error}")
                continue
                
        if not subtitles:
            st.warning("No valid subtitles found in file. Check the format.")
            
        return subtitles
    except Exception as e:
        st.error(f"Error parsing subtitle file: {e}")
        return {}

# --- Cropping Logic Functions ---
def crop_rectangular(image_cv_bgr, rect_data):
    """Crops the OpenCV BGR image using rectangle data."""
    try:
        # Validate input image
        if image_cv_bgr is None:
            st.error("No image provided for cropping")
            return None
            
        if not isinstance(image_cv_bgr, np.ndarray):
            st.error("Invalid image format for cropping")
            return None
            
        # Check if image has valid dimensions
        if len(image_cv_bgr.shape) < 2:
            st.error("Invalid image dimensions for cropping")
            return None
            
        # Validate rectangle data
        if rect_data is None or not isinstance(rect_data, dict):
            st.error("Invalid rectangle data for cropping")
            return None
            
        # Check if all required keys exist
        required_keys = ['left', 'top', 'width', 'height']
        for key in required_keys:
            if key not in rect_data:
                st.error(f"Missing '{key}' in rectangle data")
                return None
        
        try:
            left = int(rect_data['left'])
            top = int(rect_data['top'])
            width = int(rect_data['width'])
            height = int(rect_data['height'])
        except (ValueError, TypeError) as conversion_error:
            st.error(f"Invalid rectangle dimensions: {conversion_error}")
            return None
            
        # Validate dimensions
        if width <= 0 or height <= 0:
            st.warning("Please draw a valid rectangle with non-zero dimensions.")
            return None
            
        # Get image dimensions and validate
        try:
            h_img, w_img = image_cv_bgr.shape[:2]
        except Exception as shape_error:
            st.error(f"Error getting image dimensions: {shape_error}")
            return None
            
        # Clamp coordinates to image boundaries
        x1, y1 = max(0, left), max(0, top)
        x2, y2 = min(w_img, left + width), min(h_img, top + height)
        
        if x2 <= x1 or y2 <= y1:
             st.warning("Calculated crop area is outside image bounds or invalid.")
             return None
             
        # Perform the actual crop
        try:
            cropped_bgr = image_cv_bgr[y1:y2, x1:x2]
            
            # Validate crop result
            if cropped_bgr.size == 0:
                st.warning("Cropping resulted in an empty image.")
                return None
                
            return cropped_bgr
        except Exception as crop_error:
            st.error(f"Error during image cropping: {crop_error}")
            return None
    except Exception as e:
        st.error(f"Unexpected error in rectangular cropping: {e}")
        return None

def crop_freeform(image_cv_bgr, path_data):
    """Crops the OpenCV BGR image using freeform path data."""
    try:
        # Validate input image
        if image_cv_bgr is None:
            st.error("No image provided for freeform cropping")
            return None
            
        if not isinstance(image_cv_bgr, np.ndarray):
            st.error("Invalid image format for freeform cropping")
            return None
            
        # Check if image has valid dimensions
        if len(image_cv_bgr.shape) < 2:
            st.error("Invalid image dimensions for freeform cropping")
            return None
            
        # Validate path data
        if not path_data:
             st.warning("Received empty path data for freeform cropping.")
             return None
             
        if not isinstance(path_data, list):
            st.error("Invalid path data format for freeform cropping")
            return None
    
        # Get image dimensions for boundary validation
        try:
            h_img, w_img = image_cv_bgr.shape[:2]
        except Exception as shape_error:
            st.error(f"Error getting image dimensions: {shape_error}")
            return None
        
        points_list = []
        for point_idx, point_cmd in enumerate(path_data):
            try:
                if not isinstance(point_cmd, list):
                    continue
                    
                if len(point_cmd) < 3:
                    continue
                    
                # Extract coordinates
                try:
                    x = int(float(point_cmd[-2]))
                    y = int(float(point_cmd[-1]))
                except (ValueError, TypeError, IndexError) as coord_error:
                    # Skip invalid coordinates silently
                    continue
                
                # Clip coordinates to image boundaries
                x = max(0, min(x, w_img - 1))
                y = max(0, min(y, h_img - 1))
                
                # Add the valid point to our list
                points_list.append([x, y])
            except Exception as point_error:
                # Skip problematic points but log the error
                st.warning(f"Error processing point {point_idx}: {point_error}")
                continue

        # Ensure we have enough points to form a shape
        if len(points_list) < 3:
             st.warning("Not enough valid points to create a freeform crop area. Please try again with a more complete shape.")
             return None
        
        try:
            # Convert to numpy array for OpenCV
            contour = np.array(points_list, dtype=np.int32)
            
            # Create a mask with only the points inside the image
            try:
                mask = np.zeros(image_cv_bgr.shape[:2], dtype=np.uint8)
            except Exception as mask_error:
                st.error(f"Error creating mask: {mask_error}")
                return None
                
            try:
                cv2.drawContours(mask, [contour], -1, color=255, thickness=cv2.FILLED)
            except Exception as contour_error:
                st.error(f"Error drawing contours: {contour_error}")
                return None
            
            # Apply the mask
            try:
                masked_image_bgr = cv2.bitwise_and(image_cv_bgr, image_cv_bgr, mask=mask)
            except Exception as mask_apply_error:
                st.error(f"Error applying mask: {mask_apply_error}")
                return None
            
            # Calculate bounding rectangle
            try:
                x_bb, y_bb, w_bb, h_bb = cv2.boundingRect(contour)
            except Exception as bounds_error:
                st.error(f"Error calculating bounding rectangle: {bounds_error}")
                return None
            
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
            try:
                cropped_bgr = masked_image_bgr[y_bb:y_bb+h_bb, x_bb:x_bb+w_bb]
                
                # Validate the final crop
                if cropped_bgr.size == 0:
                    st.warning("Freeform cropping resulted in an empty image.")
                    return None
                    
                # Check if the crop contains any non-zero pixels
                if np.count_nonzero(cropped_bgr) == 0:
                    st.warning("Freeform crop contains only black pixels. Please try a different selection.")
                    return None
                    
                return cropped_bgr
            except Exception as crop_error:
                st.error(f"Error extracting cropped region: {crop_error}")
                return None
        
        except Exception as processing_error:
            st.error(f"Error during freeform crop processing: {processing_error}")
            return None
    
    except Exception as e:
        st.error(f"Unexpected error during freeform cropping: {e}")
        return None

# Function to get list of users from the database directory
def get_settings():
    """Load default settings from file if available, otherwise return defaults"""
    try:
        settings_path = "visual_transcription/database/default.json"
        
        # Check if settings file exists
        if not os.path.exists(settings_path):
            st.info(f"Settings file not found at {settings_path}. Using default settings.")
            return False
            
        # Try to read and parse the settings file
        try:
            with open(settings_path, 'r') as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError as json_error:
                    st.error(f"Invalid JSON in settings file: {json_error}")
                    return False
        except IOError as io_error:
            st.error(f"Error reading settings file: {io_error}")
            return False
                
        # Validate settings and load them into session state
        try:
            # Load navigation settings
            if 'frame_increment' in settings:
                try:
                    increment = int(settings['frame_increment'])
                    if increment > 0:
                        st.session_state.frame_increment = increment
                    else:
                        st.warning("Invalid frame_increment in settings (must be positive). Using default.")
                except (ValueError, TypeError):
                    st.warning("Invalid frame_increment in settings. Using default.")
                
            # Load drawing settings
            if 'stroke_slider' in settings:
                try:
                    stroke = int(settings['stroke_slider'])
                    if 1 <= stroke <= 25:  # Validate range
                        st.session_state.stroke_slider = stroke
                    else:
                        st.warning("Invalid stroke_slider in settings (must be 1-25). Using default.")
                except (ValueError, TypeError):
                    st.warning("Invalid stroke_slider in settings. Using default.")
                    
            if 'stroke_color' in settings:
                # Simple validation for hex color
                color_pattern = r'^#[0-9A-Fa-f]{6}$'
                if re.match(color_pattern, settings['stroke_color']):
                    st.session_state.stroke_color = settings['stroke_color']
                else:
                    st.warning("Invalid stroke_color format in settings. Using default.")
            
            return True
        except Exception as parsing_error:
            st.error(f"Error parsing settings values: {parsing_error}")
            return False
            
    except Exception as e:
        st.error(f"Unexpected error loading settings: {e}")
        # Use defaults if settings can't be loaded
        return False

def save_settings():
    """Save current settings to default file"""
    try:
        # Create the directory if it doesn't exist
        try:
            os.makedirs("visual_transcription/database", exist_ok=True)
        except OSError as dir_error:
            st.error(f"Error creating settings directory: {dir_error}")
            return False
        
        settings_path = "visual_transcription/database/default.json"
        
        # Validate settings and prepare them for saving
        try:
            # Get settings from session state with validation
            frame_increment = st.session_state.get('frame_increment', 1)
            if not isinstance(frame_increment, int) or frame_increment <= 0:
                frame_increment = 1
                
            stroke_slider = st.session_state.get('stroke_slider', 3)
            if not isinstance(stroke_slider, int) or stroke_slider < 1 or stroke_slider > 25:
                stroke_slider = 3
                
            stroke_color = st.session_state.get('stroke_color', '#00FF00')
            color_pattern = r'^#[0-9A-Fa-f]{6}$'
            if not re.match(color_pattern, stroke_color):
                stroke_color = '#00FF00'
            
            # Create a settings dictionary with validated values
            settings = {
                'frame_increment': frame_increment,
                'stroke_slider': stroke_slider,
                'stroke_color': stroke_color
            }
        except Exception as validation_error:
            st.error(f"Error validating settings: {validation_error}")
            return False
        
        # Write the settings to file
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
            
            return True
        except IOError as write_error:
            st.error(f"Error writing settings file: {write_error}")
            return False
    except Exception as e:
        st.error(f"Unexpected error saving settings: {e}")
        return False

# Download full transcript
def download_transcript():
    try:
        # Create document with error handling
        try:
            doc = Document()
            doc.add_heading("Visual Transcript", level=1)
        except Exception as doc_create_error:
            st.error(f"Error creating document: {doc_create_error}")
            return
        
        # Use the merged transcripts for a more comprehensive document
        try:
            merged_transcripts = merge_transcripts()
        except Exception as merge_error:
            st.error(f"Error merging transcripts: {merge_error}")
            merged_transcripts = []
        
        # Add transcript content with thorough error handling
        if merged_transcripts:
            try:
                # Add a section explaining the format
                doc.add_paragraph("This document contains both audio transcripts and visual descriptions in chronological order.")
                doc.add_paragraph("Timestamps are shown in HH:MM:SS format.")
                
                # Add all merged transcripts in chronological order
                for entry_idx, entry in enumerate(merged_transcripts):
                    try:
                        if len(entry) < 3:
                            st.warning(f"Skipping invalid transcript entry at index {entry_idx} - insufficient data")
                            continue
                            
                        if len(entry) == 3:  # Audio entry (timestamp, text, "audio")
                            try:
                                timestamp, text, source = entry
                                
                                # Validate timestamp
                                if not isinstance(timestamp, (int, float)):
                                    timestamp = 0.0
                                    
                                # Validate text
                                if not isinstance(text, str):
                                    text = str(text)
                                
                                # Format timestamp
                                try:
                                    formatted_time = seconds_to_timestamp(timestamp)
                                except Exception as time_error:
                                    st.warning(f"Error formatting timestamp: {time_error}")
                                    formatted_time = "00:00:00"
                                
                                # Add paragraph with formatting
                                try:
                                    para = doc.add_paragraph()
                                    para.add_run(f"[{formatted_time}] ").bold = True
                                    para.add_run(f"{text}")
                                except Exception as para_error:
                                    st.warning(f"Error adding audio entry paragraph: {para_error}")
                            except Exception as audio_entry_error:
                                st.warning(f"Error processing audio entry at index {entry_idx}: {audio_entry_error}")
                                continue
                        else:  # Visual entry (timestamp, text, "visual", frame_number)
                            try:
                                if len(entry) < 4:
                                    st.warning(f"Skipping invalid visual entry at index {entry_idx} - insufficient data")
                                    continue
                                    
                                timestamp, text, source, frame_number = entry
                                
                                # Validate fields
                                if not isinstance(timestamp, (int, float)):
                                    timestamp = 0.0
                                    
                                if not isinstance(text, str):
                                    text = str(text)
                                    
                                if not isinstance(frame_number, (int, str)):
                                    frame_number = str(frame_number)
                                
                                # Format timestamp
                                try:
                                    formatted_time = seconds_to_timestamp(timestamp)
                                except Exception as time_error:
                                    st.warning(f"Error formatting timestamp: {time_error}")
                                    formatted_time = "00:00:00"
                                
                                # Add paragraph with formatting
                                try:
                                    para = doc.add_paragraph()
                                    para.add_run(f"[{formatted_time} - Frame {frame_number}] ").bold = True
                                    para.add_run(f"Visual Description: {text}").italic = True
                                except Exception as para_error:
                                    st.warning(f"Error adding visual entry paragraph: {para_error}")
                            except Exception as visual_entry_error:
                                st.warning(f"Error processing visual entry at index {entry_idx}: {visual_entry_error}")
                                continue
                    except Exception as entry_error:
                        st.warning(f"Error processing entry at index {entry_idx}: {entry_error}")
                        continue
            except Exception as content_error:
                st.error(f"Error adding merged transcripts: {content_error}")
        else:
            # Fall back to original subtitles if no merged transcripts
            try:
                if "subtitles" not in st.session_state:
                    st.warning("No subtitle data available")
                    doc.add_paragraph("No transcript data available.")
                else:
                    for timestamp, text in st.session_state["subtitles"].items():
                        try:
                            # Validate timestamp
                            if not isinstance(timestamp, (int, float, str)):
                                st.warning(f"Invalid timestamp format: {timestamp}")
                                continue
                                
                            # Convert timestamp to float for formatting
                            try:
                                if isinstance(timestamp, str):
                                    timestamp_float = float(timestamp)
                                else:
                                    timestamp_float = float(timestamp)
                                formatted_time = seconds_to_timestamp(timestamp_float)
                            except (ValueError, TypeError) as time_error:
                                st.warning(f"Error converting timestamp {timestamp}: {time_error}")
                                formatted_time = str(timestamp)
                                
                            # Add paragraph
                            doc.add_paragraph(f"{formatted_time}: {text}")
                        except Exception as subtitle_error:
                            st.warning(f"Error processing subtitle: {subtitle_error}")
                            continue
            except Exception as fallback_error:
                st.error(f"Error processing fallback subtitles: {fallback_error}")
        
        # Save document to temp file
        try:
            temp_doc_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
            try:
                doc.save(temp_doc_path)
            except Exception as save_error:
                st.error(f"Error saving transcript document: {save_error}")
                return
                
            # Create download button with error handling
            try:
                with open(temp_doc_path, "rb") as doc_file:
                    try:
                        st.sidebar.download_button(
                            "Download Transcript", 
                            doc_file, 
                            file_name="visual_transcript.docx", 
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as button_error:
                        st.error(f"Error creating download button: {button_error}")
            except IOError as file_error:
                st.error(f"Error reading document file: {file_error}")
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_doc_path)
                except:
                    pass
        except Exception as temp_file_error:
            st.error(f"Error creating temporary file: {temp_file_error}")
    except Exception as e:
        st.error(f"Unexpected error in download_transcript: {e}")
        return

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
                            st.session_state.video.release()

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
                            except OSError:
                                st.warning(f"Could not delete temporary file: {temp_file_path}")


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
                
                # Instead of displaying the full prompt, just show which prompt category is active
                st.markdown(f"### Using {prompt_category} prompt")
                
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

                    # Use the canvas_key from session state to force redraw when needed
                    current_canvas_key = f"main_canvas_video_{st.session_state.canvas_key}"
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
                    except Exception as canvas_error:
                        st.error(f"Error rendering canvas: {canvas_error}")
                        canvas_result = None

                    # --- Process Canvas Result (no preview, just processing) ---
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
                                        st.success(f"Saving **cropped** frame {st.session_state.frame_number}")
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
        merged_transcripts = merge_transcripts()
        
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
                            saved_frame_data = frame_info['frame'] # This is already RGB
                            
                            # Get the image as base64 for OpenAI API
                            img_pil = Image.fromarray(saved_frame_data)
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
                            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                            gpt_response = response.json()
                            transcription = gpt_response['choices'][0]['message']['content']

                            # Update session state
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
                        except Exception as api_error:
                            st.error(f"Transcription failed: {api_error}")

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
                            if frame_number in st.session_state["frame_subtitle_map"]:
                                # Get existing subtitle text
                                subtitle_key = None
                                for start_time, text in st.session_state["subtitles"].items():
                                    if int(start_time * int(st.session_state.video.get(cv2.CAP_PROP_FPS))) == frame_number:
                                        subtitle_key = start_time
                                        break
                                
                                if subtitle_key is not None:
                                    # Add the GPT transcription to the subtitle
                                    st.session_state["subtitles"][subtitle_key] += f"\n[GPT]: {st.session_state['transcriptions'][frame_number]}"
                                    # Add this frame to the set of inserted transcriptions
                                    st.session_state.inserted_transcriptions.add(frame_number)
                                    st.success(f"Inserted GPT transcription into frame {frame_number} subtitle.")
                                else:
                                    st.warning(f"Could not find subtitle for frame {frame_number}.")
                            else:
                                # Even without a subtitle mapping, we can still track that this frame's 
                                # transcription has been inserted
                                st.session_state.inserted_transcriptions.add(frame_number)
                                st.warning(f"No subtitle mapping found for frame {frame_number}, but marked as inserted.")
                            
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
