import streamlit as st
import cv2
import tempfile
import os
import numpy as np
from PIL import Image
import json
from streamlit_drawable_canvas import st_canvas # Added
import glob # Added for listing user files

# --- Your Custom Imports ---
# Make sure these paths are correct relative to where you run the script
try:
    from visual_transcription.src.api_calls import analyze_image_Azure_Vision_Analysis, analyze_image_gpt4
    from visual_transcription.utils.initialise_LLM_models import Azure_Vision_analyse_dict
    from visual_transcription.utils.utilities import get_frame_timestamp, image_to_base64, insert_VT_into_AT
except ImportError as e:
    st.error(f"Failed to import custom modules: {e}. Ensure paths are correct and modules exist.")
    st.stop()

# --- Cropping Logic Functions (Copied from previous working example) ---

def crop_rectangular(image_cv_bgr, rect_data):
    """Crops the OpenCV BGR image using rectangle data."""
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

# -----------------------------------------------
# Initialise Session State (existing + new for crop)
# -----------------------------------------------
if "Azure Vision Add Captions" not in st.session_state:
    # Assuming Azure_Vision_analyse_dict is correctly defined/imported
    try:
        st.session_state["Azure Vision Add Captions"] = Azure_Vision_analyse_dict
    except NameError:
         st.error("Azure_Vision_analyse_dict not found. Please ensure it's defined or imported.")
         st.session_state["Azure Vision Add Captions"] = {} # Default to empty dict

if "gpt-4o" not in st.session_state:
    try:
        with open(r"visual_transcription\utils\chat_GPT.json", "r") as json_file:
            gpt4o_into = json.load(json_file)
            st.session_state['gpt-4o'] = {"prompt": gpt4o_into["prompt"], "max_words": gpt4o_into["max_words"]}
            # Initial replacement - subsequent ones happen below if user changes max_words
            st.session_state['gpt-4o']["prompt"] = st.session_state['gpt-4o']["prompt"].replace("%MAX_WORDS%", str(gpt4o_into["max_words"])) # Ensure replacement uses string
    except FileNotFoundError:
        st.error("chat_GPT.json not found. Please ensure the path is correct.")
        st.session_state['gpt-4o'] = {"prompt": "Describe the image.", "max_words": "100"} # Default fallback
    except KeyError as e:
        st.error(f"Key error loading chat_GPT.json: {e}. Check JSON structure.")
        st.session_state['gpt-4o'] = {"prompt": "Describe the image.", "max_words": "100"} # Default fallback

# Existing state variables
if "saved_frames" not in st.session_state: st.session_state.saved_frames = dict()
if 'video' not in st.session_state: st.session_state.video = None
if 'frame_number' not in st.session_state: st.session_state.frame_number = 0
if 'total_frames' not in st.session_state: st.session_state.total_frames = 0
if 'uploaded' not in st.session_state: st.session_state.uploaded = False
if "audio_transcript" not in st.session_state: st.session_state.audio_transcript = []
# Add canvas key for resetting drawings
if "canvas_key" not in st.session_state: st.session_state.canvas_key = 0
# Add frame increment for navigation - ensure it's initialized
if "frame_increment" not in st.session_state: st.session_state.frame_increment = 1
# Add settings visibility state
if "show_settings" not in st.session_state: st.session_state.show_settings = True
# Add pending video state to prevent immediate display
if "pending_video_file" not in st.session_state: st.session_state.pending_video_file = None
# Add user selection state
if "current_user" not in st.session_state: st.session_state.current_user = "default"
if "show_user_selection" not in st.session_state: st.session_state.show_user_selection = False

# Function to get list of users from the database directory
def get_users_list():
    try:
        # Get all JSON files in the database directory
        user_files = glob.glob("visual_transcription/database/*.json")
        # Extract just the filenames without extension
        users = [os.path.splitext(os.path.basename(f))[0] for f in user_files]
        # If no users found, return a default list
        if not users:
            return ["default"]
        return sorted(users)
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return ["default"]

# Function to load settings for a specific user
def load_user_settings(username):
    settings_path = f"visual_transcription/database/{username}.json"
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
                
            return True
        else:
            # If the file doesn't exist, we'll create it when saving
            return False
    except Exception as e:
        st.error(f"Error loading settings for user {username}: {e}")
        return False

# Function to save settings for a specific user
def save_user_settings(username):
    # Create the directory if it doesn't exist
    os.makedirs("visual_transcription/database", exist_ok=True)
    
    settings_path = f"visual_transcription/database/{username}.json"
    try:
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
        st.error(f"Error saving settings for user {username}: {e}")
        return False

# --- App Title and Initial Setup ---
st.title('Video Transcription Service with Cropping')

# Add user selection at the top
user_col1, user_col2, user_col3 = st.columns([2, 2, 1])
with user_col1:
    # Get list of users
    users = get_users_list()
    # Add the current user to the list if it's not already there
    if st.session_state.current_user not in users:
        users.append(st.session_state.current_user)
        users.sort()
    
    # Display current user
    st.markdown(f"**Current User:** {st.session_state.current_user}")

with user_col2:
    # Use a selectbox for user selection
    selected_user = st.selectbox(
        "Select User:",
        users,
        index=users.index(st.session_state.current_user) if st.session_state.current_user in users else 0,
        key="user_select_dropdown"
    )

with user_col3:
    # Button to load selected user settings
    if st.button("Load User", key="load_user_button"):
        if selected_user != st.session_state.current_user:
            st.session_state.current_user = selected_user
            load_user_settings(selected_user)
            st.success(f"Loaded settings for user: {selected_user}")
            st.experimental_rerun()
    
# New user creation
new_user_col1, new_user_col2, new_user_col3 = st.columns([2, 2, 1])
with new_user_col1:
    new_username = st.text_input("New Username:", key="new_username_input")

with new_user_col3:
    if st.button("Create User", key="create_user_button") and new_username:
        if new_username in users:
            st.error(f"User '{new_username}' already exists.")
        else:
            st.session_state.current_user = new_username
            st.success(f"Created new user: {new_username}")
            st.experimental_rerun()

# Simplified CSS for settings panel only
st.markdown("""
<style>
    /* Custom CSS for the settings panel */
    .settings-panel {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 10px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------
# SETTINGS PANEL (Below Title)
# -----------------------------------------------
# Check if settings should be shown or hidden
if not st.session_state.show_settings:
    # Show a button to expand settings
    col_summary, col_button = st.columns([3, 1])
    with col_summary:
        # Show a summary of the applied settings
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h6 style="margin: 0;">Applied Settings Summary</h6>
            <small>
                <b>User:</b> {3} |
                <b>Model:</b> {0} | 
                <b>Frame Increment:</b> {1} |
                <b>Audio Transcript:</b> {2}
            </small>
        </div>
        """.format(
            st.session_state.get('selected_model', 'None'),
            st.session_state.get('frame_increment', 1),
            "Loaded" if st.session_state.audio_transcript else "Not loaded",
            st.session_state.get('current_user', 'default')
        ), unsafe_allow_html=True)
    
    with col_button:
        # Only display Edit Settings button
        if st.button("⚙️ Edit Settings"):
            st.session_state.show_settings = True
            st.experimental_rerun()

# Remove the user selection section since it's been moved to the top
elif st.session_state.show_user_selection:
    # This section is no longer needed
    st.session_state.show_user_selection = False
    st.experimental_rerun()
else:
    # Use st.markdown to style the panel
    st.markdown('<div class="settings-panel">', unsafe_allow_html=True)
    
    # Use an expander for collapsible settings
    with st.expander("⚙️ Settings", expanded=True):
        st.subheader("1. Audio Transcript")
        # Load Audio Transcript if not already loaded
        if not st.session_state.audio_transcript:
            uploaded_json = st.file_uploader('Drag and drop an audio transcript file here (Optional)', type=['json'], key='audio_uploader')
            if uploaded_json is not None:
                try:
                    st.session_state.audio_transcript = json.load(uploaded_json)
                    st.success("Audio transcript loaded.")
                except json.JSONDecodeError:
                    st.error("Failed to decode JSON from audio transcript file.")
                    st.session_state.audio_transcript = []
        else:
            st.success("✅ Audio transcript loaded")
            if st.button("Clear Audio Transcript"):
                st.session_state.audio_transcript = []
                st.experimental_rerun()
        
        st.markdown("---")
        st.subheader("2. Navigation Settings")
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
        st.subheader("3. Drawing Settings")
        # Add drawing settings like in streamlit_test.py
        # Initialize default values if they don't exist in session state
        if 'stroke_slider' not in st.session_state:
            st.session_state.stroke_slider = 3
        if 'stroke_color' not in st.session_state:
            st.session_state.stroke_color = "#00FF00"
            
        # Add stroke width slider
        stroke_width = st.slider("Stroke width:", 1, 25, st.session_state.stroke_slider, key='stroke_width_input')
        if stroke_width != st.session_state.stroke_slider:
            st.session_state.stroke_slider = stroke_width
            
        # Add color picker for stroke color
        stroke_color = st.color_picker("Stroke color:", st.session_state.stroke_color, key='stroke_color_input')
        if stroke_color != st.session_state.stroke_color:
            st.session_state.stroke_color = stroke_color
            
        st.markdown("---")
        st.subheader("4. Model Selection")
        # Model selection
        model_options = ['Azure Vision Add Captions', 'gpt-4o']
        selected_model = st.selectbox('Select a model for transcription', model_options, key='model_select')
        st.session_state['selected_model'] = selected_model

        # Model-specific options
        if st.session_state['selected_model'] == "Azure Vision Add Captions":
            visual_features_model_options = ["TAGS", "OBJECTS", "CAPTION", "DENSE_CAPTIONS", "READ", "SMART_CROPS", "PEOPLE"]
            visual_features = st.multiselect('Select Azure visual features', visual_features_model_options, key='azure_features')
            if "Azure Vision Add Captions" not in st.session_state: 
                st.session_state["Azure Vision Add Captions"] = {}
            st.session_state['Azure Vision Add Captions']["visual_features"] = visual_features

        if st.session_state['selected_model'] == "gpt-4o":
            if "gpt-4o" not in st.session_state:
                st.warning("GPT-4o settings not initialized, using defaults.")
                st.session_state['gpt-4o'] = {"prompt": "Describe the image.", "max_words": "100"}

            # Display and allow editing of the max words
            prev_max_words = str(st.session_state['gpt-4o'].get("max_words", "100"))
            max_words_input = st.text_input(
                label="Max words for description",
                value=prev_max_words,
                key='gpt4_max_words'
            )
            current_max_words = str(max_words_input)

            # Update prompt if max_words changed
            current_prompt = st.session_state['gpt-4o'].get("prompt", "Describe the image in %MAX_WORDS% words.")
            if prev_max_words != current_max_words:
                st.session_state['gpt-4o']["prompt"] = current_prompt.replace(f"{prev_max_words}", f"{current_max_words}")
                st.session_state['gpt-4o']["max_words"] = current_max_words
                current_prompt = st.session_state['gpt-4o']["prompt"]

            # Display and allow editing of the full prompt
            st.session_state['gpt-4o']["prompt"] = st.text_area(
                label="Edit Prompt",
                value=current_prompt,
                height=100,
                key='gpt4_prompt_edit'
            )
        
        st.markdown("---")
        st.subheader("5. Video Upload")
        # Video uploader
        if not st.session_state.uploaded:
            uploaded_file = st.file_uploader('Drag and drop a video file', type=['mp4', 'avi', 'mov'], key='video_uploader')
            if uploaded_file is not None:
                st.success('Video upload detected! Video will be processed when you apply settings.')
                # Store the uploaded file in session state but don't process until Apply Settings
                st.session_state.pending_video_file = uploaded_file
        else:
            st.success(f"✅ Video loaded ({st.session_state.total_frames} frames)")
            if st.button("Clear Video"):
                if st.session_state.video is not None:
                    st.session_state.video.release()
                st.session_state.video = None
                st.session_state.uploaded = False
                st.session_state.saved_frames = dict()
                st.session_state.frame_number = 0
                st.session_state.total_frames = 0
                st.session_state.pending_video_file = None
                st.experimental_rerun()
        
        # Add Apply Settings button at the bottom right
        st.markdown("---")
        # Create a 3-column layout with empty space on the left to push button to right
        _, _, right_col = st.columns([3, 2, 2])
        with right_col:
            # Use a regular button
            if st.button("Apply Settings", key="apply_settings_button", type="primary"):
                # Save current user settings
                if save_user_settings(st.session_state.current_user):
                    st.success(f"Saved settings for user: {st.session_state.current_user}")
                
                # Process the pending video file if it exists
                if st.session_state.pending_video_file is not None and not st.session_state.uploaded:
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
                        st.session_state.saved_frames = dict()
                        st.session_state.frame_number = 0
                        if st.session_state.video is not None:
                            st.session_state.video.release()

                        st.session_state.video = cv2.VideoCapture(temp_file_path)
                        if st.session_state.video.isOpened():
                            st.session_state.total_frames = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_COUNT))
                            st.session_state.uploaded = True
                            st.session_state.pending_video_file = None
                            st.success(f'Video opened successfully! Total frames: {st.session_state.total_frames}')
                        else:
                            st.error('Could not open video file using OpenCV.')
                            st.session_state.uploaded = False
                            st.session_state.video = None
                            try:
                                os.unlink(temp_file_path)
                            except OSError:
                                st.warning(f"Could not delete temporary file: {temp_file_path}")
                
                # Always collapse settings when Apply Settings is pressed - moved outside the conditional
                st.session_state.show_settings = False
                st.success("Settings applied successfully!")
                st.experimental_rerun()

    # Close the panel div
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------
# MAIN CONTENT AREA (Below Settings)
# -----------------------------------------------
# Display video and controls when uploaded
if st.session_state.get("uploaded", False) and st.session_state.get("video") is not None:
    try:
        # --- Get Current Frame ---
        video_obj = st.session_state.video
        if video_obj is None or not video_obj.isOpened():
            st.error("Video object is not available or not opened. Please reload your video in the settings panel.")
            st.session_state.uploaded = False  # Reset the uploaded flag to force re-upload
        else:
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
                    # Note: This simple scaling assumes aspect ratio was maintained if resized.
                    # More robust scaling might be needed if aspect ratio changed significantly.
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
                            # Scale coordinate values (assuming they are at indices 1, 2, 3, 4...)
                            for i in range(1, len(point_cmd)):
                                scaled_cmd.append(point_cmd[i] * (scale_x if i % 2 != 0 else scale_y) ) # Scale x odd indices, y even
                            original_path_data.append(scaled_cmd)

                        current_processed_crop_bgr = crop_freeform(frame_bgr, original_path_data)
                        
                # --- Frame Navigation (moved to after image display) ---
                st.markdown("---")  # Add separator
                frame_number_input = st.slider(
                    'Select frame',
                    0,
                    max(0, st.session_state.total_frames - 1), # Ensure max is not negative if total_frames is 0
                    st.session_state.frame_number,
                    key='frame_slider'
                    )
                # Update frame number only if slider value changes
                if frame_number_input != st.session_state.frame_number:
                    # Save the original frame number to check if we actually changed frames
                    original_frame = st.session_state.frame_number
                    st.session_state.frame_number = frame_number_input
                    
                    # Clear transient crop when navigating away - added safely with try/except
                    try:
                        current_processed_crop_bgr = None
                    except:
                        pass
                        
                    # Force rerun to update the display with the new frame
                    st.experimental_rerun()

                st.write(f"Current Frame: {st.session_state.frame_number}")
                
                # --- Navigation and Save Buttons ---
                col1, col2, col3 = st.columns([1, 2, 1]) # Adjust column widths
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
                            st.experimental_rerun()  # Rerun to update frame display

                with col2:
                    # Modified Save Button
                    if st.button('💾 Save Frame (Crop if Drawn)'):
                        # Re-get the frame to ensure it's the one displayed
                        try:
                            video_obj = st.session_state.video  # Use local variable for safety
                            if video_obj and video_obj.isOpened():
                                video_obj.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
                                ret_save, frame_bgr_save = video_obj.read()

                                if ret_save:
                                    saved_image_data_rgb = None
                                    is_cropped_flag = False

                                    # Check the crop processed in *this specific script run*
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

                                    # Store in session state - ensure we're storing the numpy array directly
                                    # to avoid issues with Streamlit's media file handling
                                    try:
                                        # Create a deep copy of the numpy array to ensure it's isolated
                                        frame_copy = saved_image_data_rgb.copy()
                                        
                                        # Store in session state with clear structure
                                        st.session_state.saved_frames[st.session_state.frame_number] = {
                                            'frame': frame_copy, # Store RGB numpy array copy
                                            'frame_number': st.session_state.frame_number, # Track the original frame number
                                            'is_cropped': is_cropped_flag, # New flag
                                            'has_visual_transcripts': False,
                                            'getting_visual_transcripts': False,
                                            'visual_transcripts': None
                                            # 'time_stamp' will be added during transcription if needed
                                        }
                                        
                                        # Increment the canvas key to force a redraw/clear of the canvas
                                        st.session_state.canvas_key += 1
                                        
                                        # Clear the crop preview after saving
                                        current_processed_crop_bgr = None
                                        
                                        # Update sidebar and clear the canvas
                                        st.success(f"Saved frame {st.session_state.frame_number}")
                                        st.experimental_rerun()
                                    except Exception as save_error:
                                        st.error(f"Error saving frame: {save_error}")
                                else:
                                    st.error('Could not capture the frame to save.')
                            else:
                                st.error("Video is not available. Please reload your video in settings.")
                        except Exception as save_error:
                            st.error(f"Error saving frame: {save_error}")

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
                            st.experimental_rerun()  # Rerun to update frame display
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
        st.info("Please try uploading your video again in the settings panel.")
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
    try:
        placeholder_image_path = "visual_transcription\\image_place_holder.png"
        if os.path.exists(placeholder_image_path):
            # Display the placeholder image
            st.image(placeholder_image_path, use_column_width=True, caption="Please upload a video in the settings panel and apply settings to begin.")
        else:
            st.info("Please upload a video in the settings panel to begin.")
            st.warning(f"Note: Placeholder image not found at: {placeholder_image_path}")
    except Exception as e:
        st.info("Please upload a video in the settings panel to begin.")
        st.error(f"Error loading placeholder image: {e}")
        
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
# Sidebar: Display Saved Frames (Modified to show crop status)
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
                        st.info(f"Transcribing Frame {frame_number} using {st.session_state.get('selected_model', 'default model')}...")
                        message = None
                        response = None
                        try:
                            # Pass the saved frame data (numpy array) directly
                            saved_frame_data = frame_info['frame'] # This is already RGB

                            # --- Make API Call (Adapt based on function needs) ---
                            if st.session_state.get('selected_model') == "Azure Vision Add Captions":
                                 # Ensure client exists
                                azure_client = st.session_state.get("Azure Vision Add Captions", {}).get("client")
                                azure_features = st.session_state.get("Azure Vision Add Captions", {}).get("visual_features", [])
                                if azure_client:
                                     # Assuming analyze_image_Azure_Vision_Analysis takes RGB numpy array
                                    response = analyze_image_Azure_Vision_Analysis(saved_frame_data, azure_client, azure_features)
                                    message = response.get("message", "Error: No message in Azure response.")
                                else:
                                     message = "Error: Azure client not initialized."

                            elif st.session_state.get('selected_model') == "gpt-4o":
                                 gpt4_prompt = st.session_state.get("gpt-4o", {}).get("prompt", "Describe the image.")
                                 # Assuming analyze_image_gpt4 takes RGB numpy array
                                 response = analyze_image_gpt4(saved_frame_data, gpt4_prompt)
                                 choices = response.get("choices", [])
                                 if choices and isinstance(choices, list) and len(choices) > 0:
                                    message = choices[0].get("message", {}).get("content", "Error: No message content in GPT-4 response.")
                                 else:
                                     message = f"Error: Invalid/Empty choices in GPT-4 response: {response}"
                            else:
                                model_name = st.session_state.get('selected_model', 'Unknown')
                                message = f"Error: Model '{model_name}' not implemented."

                        except Exception as api_error:
                            st.error(f"API call failed for Frame {frame_number}: {api_error}")
                            message = f"Error during API call: {api_error}"

                        # Update session state
                        if "saved_frames" in st.session_state and frame_number in st.session_state.saved_frames:
                            st.session_state.saved_frames[frame_number]['visual_transcripts'] = message
                            st.session_state.saved_frames[frame_number]['has_visual_transcripts'] = True
                            # Get timestamp if needed
                            if st.session_state.get('video') and st.session_state.get('video').isOpened():
                                 try:
                                     video_obj = st.session_state.video  # Use local variable for safety
                                     st.session_state.saved_frames[frame_number]['time_stamp'] = get_frame_timestamp(frame_number, video_obj)
                                 except Exception as ts_error:
                                      st.warning(f"Could not get timestamp for Frame {frame_number}: {ts_error}")
                                      st.session_state.saved_frames[frame_number]['time_stamp'] = "N/A"
                            else:
                                 st.warning("Video object not available for timestamp.")
                                 st.session_state.saved_frames[frame_number]['time_stamp'] = "N/A"

                            st.success(f"Transcription updated for Frame {frame_number}.")
                            st.experimental_rerun()  # Update sidebar display

            with col2_side:
                # Add to Transcript / Remove Button
                if frame_info.get('has_visual_transcripts', False):
                    if st.button(f"Add #{frame_number} to Final", key=f"add_{frame_number}"):
                        try:
                            insert_VT_into_AT(frame_info)
                            st.success(f"Frame {frame_number} info added to audio transcript.")
                            st.experimental_rerun()
                        except NameError:
                             st.error("Function 'insert_VT_into_AT' not found.")
                        except Exception as insert_err:
                             st.error(f"Error adding Frame {frame_number} to transcript: {insert_err}")

                # Add a button to remove a frame from selection
                if st.button(f"Remove #{frame_number}", key=f"del_{frame_number}"):
                     if "saved_frames" in st.session_state and frame_number in st.session_state.saved_frames:
                          del st.session_state.saved_frames[frame_number]
                          st.success(f"Removed Frame {frame_number} from selection.")
                          st.experimental_rerun()  # Update sidebar

# --- Display Final Transcript Information ---
st.markdown("---")
st.subheader("Combined Transcript (Preview)")
st.write(st.session_state.audio_transcript)

# -----------------------------------------------
# Add Some Spacing at the Bottom
# -----------------------------------------------
st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

# Note: Video release logic might be needed, e.g., using atexit or explicit button
# if st.session_state.video is not None:
#     st.session_state.video.release()