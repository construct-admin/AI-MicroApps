import streamlit as st
import os
import json
import hashlib
import shutil
import glob
import pickle
from datetime import datetime
import numpy as np
import io
import cv2
import logging
from logging.handlers import RotatingFileHandler
import sys

# Set up logging
logs_dir = os.path.join("database", "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logger
logger = logging.getLogger("login_logger")
logger.setLevel(logging.INFO)

# Create handlers
log_file = os.path.join(logs_dir, "login.log")
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
console_handler = logging.StreamHandler(sys.stdout)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Login module initialized")

def hash_password(password):
    """Simple password hashing using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_folder_structure(username):
    """Create the folder structure for a new user"""
    logger.info(f"Creating folder structure for user: {username}")
    
    # Create user directory if it doesn't exist
    user_dir = os.path.join("database", "users", username)
    os.makedirs(user_dir, exist_ok=True)
    logger.debug(f"Created user directory: {user_dir}")
    
    # Create history subdirectory
    history_dir = os.path.join(user_dir, "history")
    os.makedirs(history_dir, exist_ok=True)
    logger.debug(f"Created history directory: {history_dir}")
    
    # Create projects subdirectory
    projects_dir = os.path.join(user_dir, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    logger.debug(f"Created projects directory: {projects_dir}")
    
    # Create empty user_configurations.json file with default settings
    config_file = os.path.join(user_dir, "user_configurations.json")
    if not os.path.exists(config_file):
        default_settings = {
            "frame_increment": 1,
            "stroke_slider": 3,
            "stroke_color": "#00FF00",
            "max_words": "100",
            "prompt_category": "general"
        }
        with open(config_file, "w") as f:
            json.dump(default_settings, f, indent=4)
        logger.debug(f"Created default user configurations file: {config_file}")
    
    logger.info(f"Successfully created folder structure for user: {username}")
    return True

def get_users():
    """Get list of registered users from the users directory"""
    users_dir = os.path.join("database", "users")
    users = {}
    
    # Create users directory if it doesn't exist
    os.makedirs(users_dir, exist_ok=True)
    
    # Check credentials file first
    credentials_file = os.path.join("database", "credentials.json")
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, "r") as f:
                users = json.load(f)
            logger.debug(f"Loaded {len(users)} users from credentials file")
        except Exception as e:
            logger.error(f"Error loading credentials file: {e}")
    else:
        logger.debug("Credentials file not found, returning empty users dictionary")
    
    return users

def save_users(users):
    """Save users dictionary to credentials file"""
    credentials_file = os.path.join("database", "credentials.json")
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
    
    try:
        with open(credentials_file, "w") as f:
            json.dump(users, f, indent=4)
        logger.info(f"Saved {len(users)} users to credentials file")
    except Exception as e:
        logger.error(f"Error saving users to credentials file: {e}")

def get_user_settings(username):
    """Load user-specific settings"""
    settings_path = os.path.join("database", "users", username, "user_configurations.json")
    
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
            logger.debug(f"Loaded settings for user: {username}")
            return settings
        except Exception as e:
            logger.error(f"Error loading user settings for {username}: {e}")
            st.error(f"Error loading user settings: {e}")
    else:
        logger.warning(f"Settings file not found for user: {username}, using defaults")
    
    # Return default settings if file doesn't exist or has an error
    return {
        "frame_increment": 1,
        "stroke_slider": 3,
        "stroke_color": "#00FF00",
        "max_words": "100",
        "prompt_category": "general"
    }

def save_user_settings(username, settings):
    """Save user-specific settings"""
    if not username:
        logger.error("Attempted to save settings with empty username")
        return False
    
    settings_path = os.path.join("database", "users", username, "user_configurations.json")
    
    # Ensure user directory exists
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    
    try:
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4)
        logger.info(f"Settings saved successfully for user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error saving settings for user {username}: {e}")
        st.error(f"Error saving user settings: {e}")
        return False

def get_user_projects(username):
    """Get list of projects for a specific user"""
    projects_dir = os.path.join("database", "users", username, "projects")
    
    # Ensure directory exists
    os.makedirs(projects_dir, exist_ok=True)
    
    # Get all project directories
    projects = []
    for project_dir in glob.glob(os.path.join(projects_dir, "*")):
        if os.path.isdir(project_dir):
            project_name = os.path.basename(project_dir)
            
            # Try to load project info
            info_file = os.path.join(project_dir, "project_info.json")
            created_date = "Unknown date"
            
            if os.path.exists(info_file):
                try:
                    with open(info_file, "r") as f:
                        info = json.load(f)
                        created_date = info.get("created_date", "Unknown date")
                except Exception as e:
                    logger.warning(f"Error reading project info for {project_name}: {e}")
                    pass
                    
            projects.append({
                "name": project_name,
                "path": project_dir,
                "created_date": created_date
            })
    
    logger.debug(f"Found {len(projects)} projects for user: {username}")        
    return sorted(projects, key=lambda x: x["name"])

def create_new_project(username, project_name):
    """Create a new project folder structure for a user"""
    if not username or not project_name:
        logger.error(f"Attempted to create project with invalid parameters: username={username}, project_name={project_name}")
        return False
        
    # Sanitize project name (remove special characters, replace spaces with underscores)
    safe_project_name = "".join(c if c.isalnum() else "_" for c in project_name)
    
    # Create project directory
    project_dir = os.path.join("database", "users", username, "projects", safe_project_name)
    
    # Check if project already exists
    if os.path.exists(project_dir):
        logger.warning(f"Project already exists: {project_name} for user: {username}")
        return False
        
    # Create project directory and subfolders
    logger.info(f"Creating new project: {project_name} for user: {username}")
    try:
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "frames"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "transcripts"), exist_ok=True)
        
        # Create project info file
        info_file = os.path.join(project_dir, "project_info.json")
        project_info = {
            "name": project_name,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": username,
            "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(info_file, "w") as f:
            json.dump(project_info, f, indent=4)
            
        # Set the current project in session state
        st.session_state.current_project = {
            "name": project_name,
            "path": project_dir,
            "created_date": project_info["created_date"]
        }
        
        logger.info(f"Project created successfully: {project_name} for user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error creating project {project_name} for user {username}: {e}")
        return False

def save_project_data(username, project_name):
    """Save the current project state including video, audio transcripts, and frames"""
    if not username or not project_name:
        logger.error(f"Attempted to save project with invalid parameters: username={username}, project_name={project_name}")
        return False, "Username or project name is missing"
    
    logger.info(f"Saving project data for {project_name} (user: {username})")
    try:
        # Get the project directory path
        safe_project_name = "".join(c if c.isalnum() else "_" for c in project_name)
        project_dir = os.path.join("database", "users", username, "projects", safe_project_name)
        
        # Ensure the project directory exists
        if not os.path.exists(project_dir):
            logger.debug(f"Project directory does not exist, creating: {project_dir}")
            os.makedirs(project_dir, exist_ok=True)
        
        # Save frames to the frames directory
        frames_dir = os.path.join(project_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        # Clear existing frames to avoid conflicts
        for old_frame in glob.glob(os.path.join(frames_dir, "*.jpg")):
            try:
                os.remove(old_frame)
            except Exception as e:
                logger.warning(f"Could not remove old frame {old_frame}: {e}")
        
        # Save each frame as an image file
        saved_frames = st.session_state.get("saved_frames", {})
        logger.info(f"Saving {len(saved_frames)} frames to project directory")
        
        frames_saved = 0
        for frame_number, frame_info in saved_frames.items():
            if 'frame' in frame_info and frame_info['frame'] is not None:
                try:
                    from PIL import Image
                    import numpy as np
                    # Convert frame to a PIL Image
                    if isinstance(frame_info['frame'], np.ndarray):
                        img = Image.fromarray(frame_info['frame'])
                    else:
                        img = frame_info['frame']
                    # Save the image
                    img.save(os.path.join(frames_dir, f"frame_{frame_number}.jpg"))
                    frames_saved += 1
                except Exception as e:
                    logger.error(f"Error saving frame {frame_number}: {e}")
        
        logger.debug(f"Successfully saved {frames_saved} frames")
        
        # Save transcriptions to the transcripts directory
        transcripts_dir = os.path.join(project_dir, "transcripts")
        os.makedirs(transcripts_dir, exist_ok=True)
        
        # Save transcriptions as JSON
        transcriptions = st.session_state.get("transcriptions", {})
        transcriptions_file = os.path.join(transcripts_dir, "transcriptions.json")
        try:
            with open(transcriptions_file, "w") as f:
                # Convert frame numbers from int to str for JSON serialization
                json_transcriptions = {str(k): v for k, v in transcriptions.items()}
                json.dump(json_transcriptions, f, indent=4)
            logger.debug(f"Saved {len(transcriptions)} transcriptions to file")
        except Exception as e:
            logger.error(f"Error saving transcriptions: {e}")
        
        # Save subtitles
        subtitles = st.session_state.get("subtitles", {})
        subtitles_file = os.path.join(transcripts_dir, "subtitles.json")
        try:
            with open(subtitles_file, "w") as f:
                # Convert timestamp keys to strings for JSON serialization
                json_subtitles = {str(k): v for k, v in subtitles.items()}
                json.dump(json_subtitles, f, indent=4)
            logger.debug(f"Saved {len(subtitles)} subtitles to file")
        except Exception as e:
            logger.error(f"Error saving subtitles: {e}")
        
        # Save inserted_transcriptions
        inserted = list(st.session_state.get("inserted_transcriptions", set()))
        inserted_file = os.path.join(transcripts_dir, "inserted_transcriptions.json")
        try:
            with open(inserted_file, "w") as f:
                # Convert any integers to strings for JSON compatibility
                string_inserted = [str(i) for i in inserted]
                json.dump(string_inserted, f, indent=4)
            logger.debug(f"Saved {len(inserted)} inserted transcriptions")
        except Exception as e:
            logger.error(f"Error saving inserted transcriptions: {e}")
            
        # Save frame metadata (separate from the images)
        frame_metadata = {}
        for frame_number, frame_info in saved_frames.items():
            # Extract metadata without the actual frame data to avoid duplication
            metadata = {
                'has_visual_transcripts': frame_info.get('has_visual_transcripts', False),
                'time_stamp': frame_info.get('time_stamp', 0.0),
                'is_cropped': frame_info.get('is_cropped', False)
            }
            frame_metadata[str(frame_number)] = metadata
            
        metadata_file = os.path.join(transcripts_dir, "frame_metadata.json")
        try:
            with open(metadata_file, "w") as f:
                json.dump(frame_metadata, f, indent=4)
            logger.debug(f"Saved metadata for {len(frame_metadata)} frames")
        except Exception as e:
            logger.error(f"Error saving frame metadata: {e}")
        
        # Save project state metadata
        project_state = {
            "frame_number": st.session_state.get("frame_number", 0),
            "total_frames": st.session_state.get("total_frames", 0),
            "frame_increment": st.session_state.get("frame_increment", 1),
            "stroke_slider": st.session_state.get("stroke_slider", 3),
            "stroke_color": st.session_state.get("stroke_color", "#00FF00"),
            "max_words": st.session_state.get("max_words", "100"),
            "prompt_category": st.session_state.get("prompt_category", "general"),
            "uploaded": st.session_state.get("uploaded", False),
            "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save project state
        state_file = os.path.join(project_dir, "project_state.json")
        try:
            with open(state_file, "w") as f:
                json.dump(project_state, f, indent=4)
            logger.debug("Saved project state metadata")
        except Exception as e:
            logger.error(f"Error saving project state: {e}")
        
        # Create directories if they don't exist
        video_dir = os.path.join(project_dir, "videos")
        srt_dir = os.path.join(project_dir, "srt")
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(srt_dir, exist_ok=True)
        
        # Try to save the video file if it exists in session state
        video_saved = False
        if "video" in st.session_state and st.session_state.video is not None:
            logger.info("Attempting to save video file")
            try:
                # Save the video using OpenCV's VideoCapture object
                video_path = os.path.join(video_dir, "project_video.mp4")
                
                # Get the video properties from the VideoCapture object
                cap = st.session_state.video
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                # Create a VideoWriter object - try using more compatible codecs
                # Try H.264 codec ('avc1') which has better compatibility
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
                
                # If avc1 fails, try mp4v as fallback
                if not out.isOpened():
                    logger.warning("Failed to initialize VideoWriter with 'avc1' codec, trying 'mp4v'")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
                    
                    # If mp4v also fails, try XVID as a last resort
                    if not out.isOpened():
                        logger.warning("Failed to initialize VideoWriter with 'mp4v' codec, trying 'XVID'")
                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                        alt_video_path = os.path.join(video_dir, "project_video.avi")
                        out = cv2.VideoWriter(alt_video_path, fourcc, fps, (width, height))
                        video_path = alt_video_path
                
                if not out.isOpened():
                    raise Exception("Could not initialize VideoWriter with any codec")
                    
                # Save the current position to restore it later
                current_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                
                # Reset to the beginning of the video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                # Write all frames to the output video
                frames_written = 0
                for i in range(total_frames):
                    ret, frame = cap.read()
                    if ret:
                        out.write(frame)
                        frames_written += 1
                    else:
                        break
                
                # Release the VideoWriter
                out.release()
                
                # Restore the original position
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
                
                video_saved = True
                logger.info(f"Video saved successfully: {video_path} ({frames_written} frames)")
            except Exception as e:
                logger.error(f"Error saving video file: {e}")
                st.error(f"Error saving video file: {e}")
        
        # Try to save the SRT file if it exists
        srt_path = os.path.join(srt_dir, "subtitles.srt")
        srt_saved = False
        if "srt_data" in st.session_state and st.session_state.srt_data is not None:
            logger.info("Attempting to save SRT file")
            try:
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(st.session_state.srt_data)
                srt_saved = True
                logger.info(f"SRT file saved successfully: {srt_path}")
            except Exception as e:
                logger.error(f"Error saving SRT file: {e}")
                st.error(f"Error saving SRT file: {e}")
                
        # Update project info with video and SRT status
        project_info = json.load(open(os.path.join(project_dir, "project_info.json")))
        project_info["video_saved"] = video_saved
        project_info["srt_saved"] = srt_saved
        project_info["saved_frames_count"] = len(saved_frames)
        project_info["transcriptions_count"] = len(transcriptions)
        
        with open(os.path.join(project_dir, "project_info.json"), "w") as f:
            json.dump(project_info, f, indent=4)
        
        success_message = "Project saved successfully"
        if video_saved and srt_saved:
            success_message += " (including video and subtitles)"
        elif video_saved:
            success_message += " (including video)"
        elif srt_saved:
            success_message += " (including subtitles)"
        
        logger.info(f"Project {project_name} saved successfully for user {username}")    
        return True, success_message
    except Exception as e:
        logger.error(f"Error saving project {project_name} for user {username}: {e}")
        return False, f"Error saving project: {e}"

def load_project_data(project_name):
    """
    Load saved project data from the user's directory
    """
    logger.info(f"Attempting to load project: {project_name}")
    
    project_dir = os.path.join('database', 'users', st.session_state.current_user, 'projects', project_name)
    
    # Check if the project directory exists
    if not os.path.exists(project_dir):
        logger.error(f"Project directory not found: {project_dir}")
        return False, f"Project directory not found: {project_dir}"
    
    try:
        # Load project state
        project_state_file = os.path.join(project_dir, "project_state.json")
        if os.path.exists(project_state_file):
            try:
                with open(project_state_file, "r") as f:
                    project_state = json.load(f)
                    for key, value in project_state.items():
                        st.session_state[key] = value
                logger.debug(f"Loaded project state: {project_state_file}")
            except Exception as e:
                logger.error(f"Error loading project state: {e}")
        
        # Load project info
        info_file = os.path.join(project_dir, "project_info.json")
        project_info = None
        if os.path.exists(info_file):
            try:
                with open(info_file, "r") as f:
                    project_info = json.load(f)
                st.session_state.project_info = project_info
                logger.debug(f"Loaded project info: {info_file}")
            except Exception as e:
                logger.error(f"Error loading project info: {e}")
        
        # Load saved frames
        saved_frames_dir = os.path.join(project_dir, "frames")
        if os.path.exists(saved_frames_dir):
            frames_loaded = 0
            saved_frames = {}
            
            # First, load transcriptions if available to use with the frames
            transcriptions_file = os.path.join(project_dir, "transcripts", "transcriptions.json")
            transcriptions = {}
            if os.path.exists(transcriptions_file):
                try:
                    with open(transcriptions_file, "r") as f:
                        transcriptions = json.load(f)
                        logger.debug(f"Loaded transcriptions for use with frames")
                except Exception as e:
                    logger.error(f"Error loading transcriptions for frames: {e}")
            
            # Load frames from JPG files
            for frame_file in os.listdir(saved_frames_dir):
                if frame_file.endswith(".jpg") and frame_file.startswith("frame_"):
                    try:
                        # Extract frame number from filename (frame_123.jpg -> 123)
                        frame_number = int(frame_file.split("_")[1].split(".")[0])
                        frame_path = os.path.join(saved_frames_dir, frame_file)
                        
                        # Load the image
                        from PIL import Image
                        img = Image.open(frame_path)
                        frame_data = np.array(img)
                        
                        # Create frame info structure
                        frame_info = {
                            'frame': frame_data,
                            'has_visual_transcripts': False,
                            'time_stamp': 0.0
                        }
                        
                        # Add transcription if available
                        if str(frame_number) in transcriptions:
                            frame_info['visual_transcripts'] = transcriptions[str(frame_number)]
                            frame_info['has_visual_transcripts'] = True
                        
                        # Add to saved_frames
                        saved_frames[frame_number] = frame_info
                        frames_loaded += 1
                    except Exception as e:
                        logger.warning(f"Error loading frame {frame_file}: {e}")
            
            # Load frame metadata if available
            metadata_file = os.path.join(project_dir, "transcripts", "frame_metadata.json")
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, "r") as f:
                        frame_metadata = json.load(f)
                        
                    # Apply metadata to the frames we loaded
                    for frame_number_str, metadata in frame_metadata.items():
                        try:
                            frame_number = int(frame_number_str)
                            if frame_number in saved_frames:
                                # Update with metadata properties
                                for key, value in metadata.items():
                                    saved_frames[frame_number][key] = value
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Error applying metadata to frame {frame_number_str}: {e}")
                            
                    logger.debug(f"Applied metadata to frames from {metadata_file}")
                except Exception as e:
                    logger.error(f"Error loading frame metadata: {e}")
                    
            # Load inserted transcriptions
            inserted_file = os.path.join(project_dir, "transcripts", "inserted_transcriptions.json")
            if os.path.exists(inserted_file):
                try:
                    with open(inserted_file, "r") as f:
                        inserted_list = json.load(f)
                        # Convert to integers and add to set
                        inserted_set = set()
                        for item in inserted_list:
                            try:
                                inserted_set.add(int(item))
                            except ValueError:
                                inserted_set.add(item)
                        st.session_state.inserted_transcriptions = inserted_set
                    logger.debug(f"Loaded {len(inserted_set)} inserted transcriptions")
                except Exception as e:
                    logger.error(f"Error loading inserted transcriptions: {e}")
            
            # Add the loaded frames to session state
            st.session_state.saved_frames = saved_frames
            logger.debug(f"Loaded {frames_loaded} frames from {saved_frames_dir}")
        
        # Load transcriptions (general loading, not just for frames)
        transcriptions_file = os.path.join(project_dir, "transcripts", "transcriptions.json")
        if os.path.exists(transcriptions_file):
            try:
                with open(transcriptions_file, "r") as f:
                    transcriptions = json.load(f)
                    # Convert string keys back to integers if needed
                    int_transcriptions = {}
                    for k, v in transcriptions.items():
                        try:
                            int_transcriptions[int(k)] = v
                        except ValueError:
                            int_transcriptions[k] = v
                    st.session_state.transcriptions = int_transcriptions
                logger.debug(f"Loaded transcriptions: {transcriptions_file}")
            except Exception as e:
                logger.error(f"Error loading transcriptions: {e}")

        # Load subtitles from JSON file (primary method)
        subtitles_file = os.path.join(project_dir, "transcripts", "subtitles.json")
        subtitles_loaded = False
        if os.path.exists(subtitles_file):
            try:
                with open(subtitles_file, "r") as f:
                    json_subtitles = json.load(f)
                    # Convert keys back to float for timestamp keys
                    subtitles = {}
                    for k, v in json_subtitles.items():
                        try:
                            subtitles[float(k)] = v
                        except ValueError:
                            subtitles[k] = v
                    st.session_state.subtitles = subtitles
                    subtitles_loaded = True
                logger.debug(f"Loaded {len(subtitles)} subtitles from JSON file")
                
                # Map subtitles to frame numbers if video is loaded
                if subtitles_loaded and st.session_state.get('video') and st.session_state.video.isOpened():
                    fps = st.session_state.video.get(cv2.CAP_PROP_FPS)
                    if fps > 0:
                        # Map subtitles to frame numbers
                        frame_subtitle_count = 0
                        st.session_state["frame_subtitle_map"] = {}
                        
                        for start_time, text in st.session_state["subtitles"].items():
                            try:
                                # Make sure start_time is treated as a float
                                start_time_float = float(start_time)
                                frame_num = int(start_time_float * fps)
                                st.session_state["frame_subtitle_map"][frame_num] = text
                                frame_subtitle_count += 1
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Error mapping subtitle with timestamp {start_time}: {e}")
                                
                        logger.info(f"Mapped {frame_subtitle_count} subtitles to frames from JSON")
                    else:
                        logger.warning("Could not get valid FPS from video for subtitle mapping")
            except Exception as e:
                logger.error(f"Error loading subtitles from JSON: {e}")
                st.warning(f"Error loading subtitles file: {e}")
        
        # Load video file if available
        video_path = os.path.join(project_dir, "videos", "project_video.mp4")
        logger.debug(f"Checking for video at: {video_path}")
        if os.path.exists(video_path):
            logger.info(f"Video file found at: {video_path}")
            try:
                # Read the video file and set up st.session_state.video
                logger.debug("Attempting to read video file with OpenCV")
                st.session_state.video = cv2.VideoCapture(video_path)
                
                if st.session_state.video.isOpened():
                    logger.debug("Video file successfully opened with OpenCV")
                    # Create BytesIO object for st.session_state.video_file
                    logger.debug("Creating BytesIO object for video file")
                    with open(video_path, "rb") as f:
                        video_bytes = f.read()
                    
                    # Create a BytesIO object to simulate the uploaded file
                    video_file = io.BytesIO(video_bytes)
                    video_file.name = "project_video.mp4"
                    st.session_state.video_file = video_file
                    logger.debug("BytesIO object created and stored in session state")
                    
                    # Set uploaded flag
                    st.session_state.uploaded = True
                    logger.debug("Uploaded flag set to True")
                    
                    # Get video properties
                    logger.debug("Getting video properties")
                    width = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = st.session_state.video.get(cv2.CAP_PROP_FPS)
                    frame_count = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_COUNT))
                    logger.info(f"Video properties: {width}x{height}, {fps} fps, {frame_count} frames")
                    
                    # Store video properties
                    st.session_state.video_properties = {
                        "width": width,
                        "height": height,
                        "fps": fps,
                        "frame_count": frame_count
                    }
                    logger.debug("Video properties stored in session state")
                else:
                    logger.error("Video file could not be opened with OpenCV")
            except Exception as e:
                logger.error(f"Error loading video: {e}")
                print(f"Error loading video: {e}")
        else:
            logger.warning("Video file not found")
        
        # Load SRT file if available
        srt_path = os.path.join(project_dir, "srt", "subtitles.srt")
        srt_loaded = False
        
        # First check if subtitles were already loaded from JSON
        if not subtitles_loaded and os.path.exists(srt_path):
            try:
                with open(srt_path, "r", encoding="utf-8") as f:
                    srt_data = f.read()
                
                # Store the SRT data
                st.session_state.srt_data = srt_data
                # Note: We can't set st.session_state.srt_uploader directly as it's a widget
                # Instead, set a flag to indicate SRT is loaded from file
                st.session_state.srt_file_loaded = True
                logger.debug(f"Loaded SRT data from: {srt_path}")
                
                # Import parse_srt from visual_transcripts.py
                try:
                    # Try direct import first
                    from visual_transcripts import parse_srt as parse_srt_func
                    logger.debug("Imported parse_srt function directly")
                except ImportError:
                    # Fall back to dynamic import
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("visual_transcripts", 
                                                                     "visual_transcripts.py")
                        visual_transcripts = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(visual_transcripts)
                        parse_srt_func = visual_transcripts.parse_srt
                        logger.debug("Imported parse_srt function from visual_transcripts.py")
                    except Exception as imp_err:
                        logger.error(f"Error importing parse_srt: {imp_err}")
                        # Define a simple fallback parse function if import fails
                        def parse_srt_func(data):
                            if isinstance(data, io.BytesIO):
                                data = data.read().decode('utf-8')
                            if isinstance(data, bytes):
                                data = data.decode('utf-8')
                            subtitles = {}
                            try:
                                lines = data.split("\n")
                                index, start_time = None, None
                                for line in lines:
                                    line = line.strip()
                                    if line.isdigit():
                                        index = int(line)
                                    elif "-->" in line:
                                        start_time = line.split(" --> ")[0]
                                        start_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(start_time.replace(',', '.').split(':'))))
                                    elif line and start_time is not None:
                                        subtitles[start_time] = line
                                        start_time = None
                                logger.warning(f"Used fallback SRT parser, found {len(subtitles)} subtitles")
                            except Exception as parse_err:
                                logger.error(f"Fallback SRT parser failed: {parse_err}")
                            return subtitles
                
                # Only parse SRT if subtitles weren't already loaded from JSON
                if not subtitles_loaded:
                    # Parse the SRT data directly - don't use BytesIO approach that might conflict with the widget
                    try:
                        st.session_state.subtitles = parse_srt_func(srt_data)
                        logger.debug(f"Parsed {len(st.session_state.subtitles)} subtitles from SRT data")
                        srt_loaded = True
                    except Exception as e:
                        logger.error(f"Error parsing SRT file: {e}")
                        # Try again with different parsing method
                        try:
                            # Create a temporary object just for parsing
                            srt_bytes = srt_data.encode('utf-8')
                            io_obj = io.BytesIO(srt_bytes)
                            io_obj.name = "temp_subtitles.srt"
                            st.session_state.subtitles = parse_srt_func(io_obj)
                            logger.debug(f"Parsed {len(st.session_state.subtitles)} subtitles using BytesIO")
                            srt_loaded = True
                        except Exception as e2:
                            logger.error(f"Second attempt at parsing SRT failed: {e2}")
                
                # Update project info
                if srt_loaded and project_info:
                    project_info["srt_saved"] = True
                    try:
                        with open(os.path.join(project_dir, "project_info.json"), "w") as f:
                            json.dump(project_info, f, indent=4)
                    except Exception as e:
                        logger.error(f"Error updating project info with SRT status: {e}")
                
            except Exception as e:
                logger.error(f"Error loading SRT: {e}")
                st.warning(f"Error loading subtitle file: {e}")
        elif not subtitles_loaded:
            logger.warning(f"SRT file not found at: {srt_path}")
        elif subtitles_loaded:
            logger.info("Using subtitles loaded from JSON file instead of processing SRT")
            
        # If SRT file was found but couldn't be loaded and subtitles aren't loaded from JSON, show a warning
        if not subtitles_loaded and os.path.exists(srt_path) and not srt_loaded:
            st.warning("Found an SRT subtitle file but encountered errors loading it. Check the logs for details.")
        
        # Update the current project - use dictionary format for consistency
        try:
            # Format current_project as dictionary like in create_new_project
            st.session_state.current_project = {
                "name": project_name,
                "path": project_dir,
                "created_date": project_info.get("created_date") if project_info else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.info(f"Set current_project as dictionary with name: {project_name}")
        except Exception as e:
            # Fall back to string if needed
            st.session_state.current_project = project_name
            logger.warning(f"Failed to set current_project as dictionary, using string instead: {project_name}")
        
        logger.info(f"Project {project_name} loaded successfully")
        
        return True, "Project loaded successfully"
    except Exception as e:
        logger.error(f"Error loading project {project_name}: {e}")
        return False, f"Error loading project: {e}"

def project_selection_screen():
    """Display project selection screen"""
    st.title(f"Welcome, {st.session_state.current_user}!")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create New Project")
        project_name = st.text_input("Project Name", key="new_project_name")
        
        if st.button("Create Project", type="primary"):
            if not project_name:
                st.error("Please enter a project name")
            else:
                if create_new_project(st.session_state.current_user, project_name):
                    st.success(f"Project '{project_name}' created successfully!")
                    # Set project selected flag to continue to main app
                    st.session_state.project_selected = True
                    st.experimental_rerun()
                else:
                    st.error(f"Project '{project_name}' already exists or could not be created.")
    
    with col2:
        st.subheader("Load Existing Project")
        # Get user's projects
        projects = get_user_projects(st.session_state.current_user)
        
        if not projects:
            st.info("No existing projects found. Create a new project to get started.")
        else:
            # Create a selection box with project names
            project_options = [f"{p['name']} (Created: {p['created_date']})" for p in projects]
            selected_project_idx = st.selectbox(
                "Select a project to load",
                range(len(project_options)),
                format_func=lambda x: project_options[x],
                key="project_selector"
            )
            
            if st.button("Load Project", type="primary"):
                selected_project = projects[selected_project_idx]
                # Store the selected project in session state
                st.session_state.current_project = selected_project
                
                # Load project data
                success, message = load_project_data(selected_project['name'])
                if success:
                    # Set project selected flag to continue to main app
                    st.session_state.project_selected = True
                    st.success(f"Project '{selected_project['name']}' loaded successfully!")
                else:
                    st.warning(f"Project loaded with some issues: {message}")
                    # Still continue with the project
                    st.session_state.project_selected = True
                
                st.experimental_rerun()
    
    # Display a placeholder image
    try:
        placeholder_image_path = "image_place_holder.png"
        if os.path.exists(placeholder_image_path):
            from PIL import Image
            placeholder_img = Image.open(placeholder_image_path)
            placeholder_img = placeholder_img.resize((720, 480))
            st.image(placeholder_img, caption="VT Generator - Visual Transcription Service")
    except Exception as e:
        st.info("VT Generator - Visual Transcription Service")
    
    # Add a logout button at the bottom
    if st.button("Logout", key="project_screen_logout"):
        logout()
        st.experimental_rerun()

def login_screen():
    """Display login screen and handle authentication"""
    logger.debug("Rendering login screen")
    
    # Initialize key session state variables if not present
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
        
    if "project_selected" not in st.session_state:
        st.session_state.project_selected = False
    
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    
    # If already logged in but no project selected, show project selection screen
    if st.session_state.logged_in and not st.session_state.project_selected:
        logger.debug(f"User {st.session_state.current_user} is logged in but no project selected")
        # First load user settings
        if "user_settings_loaded" not in st.session_state or not st.session_state.user_settings_loaded:
            username = st.session_state.current_user
            logger.debug(f"Loading settings for user: {username}")
            user_settings = get_user_settings(username)
            
            # Update session state with user settings
            st.session_state.frame_increment = user_settings.get("frame_increment", 1)
            st.session_state.stroke_slider = user_settings.get("stroke_slider", 3)
            st.session_state.stroke_color = user_settings.get("stroke_color", "#00FF00")
            st.session_state["max_words"] = user_settings.get("max_words", "100")
            st.session_state.prompt_category = user_settings.get("prompt_category", "general")
            
            # Mark settings as loaded
            st.session_state.user_settings_loaded = True
            logger.debug(f"Settings loaded for user: {username}")
        
        # Show project selection screen
        project_selection_screen()
        return False
    
    # If logged in and project selected, continue to main app
    if st.session_state.logged_in and st.session_state.project_selected:
        logger.debug(f"User {st.session_state.current_user} logged in with project {st.session_state.current_project} selected")
        return True
    
    # If not logged in, show login screen
    st.title("VT Generator Login")
    
    # Get registered users
    users = get_users()
    
    # Create tabs for Login and Register
    login_tab, register_tab = st.tabs(["Login", "Create New User"])
    
    # Login tab
    with login_tab:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In"):
            logger.info(f"Login attempt: {username}")
            if username in users and users[username] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.user_settings_loaded = False  # Mark settings to be loaded
                st.session_state.project_selected = False  # Reset project selection
                logger.info(f"User {username} logged in successfully")
                st.success(f"Welcome back, {username}!")
                # Force a rerun to update the UI after login
                st.experimental_rerun()
                return False
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                st.error("Invalid username or password")
                return False
    
    # Register tab
    with register_tab:
        st.header("Create New User")
        
        # Add registration tracking flags
        if "registration_success" not in st.session_state:
            st.session_state.registration_success = False
        
        # Add a form key counter that gets incremented to force form reset
        if "form_reset_key" not in st.session_state:
            st.session_state.form_reset_key = 0
            
        # If registration was successful, display a success message
        if st.session_state.registration_success:
            st.success("Account created successfully! You can now login with your new account.")
            # Reset the success flag
            st.session_state.registration_success = False
        
        # Use the form reset key in the widget keys to force form reset
        form_key_suffix = st.session_state.form_reset_key
        new_username = st.text_input("Choose a Username", key=f"register_username_{form_key_suffix}")
        new_password = st.text_input("Choose a Password", type="password", key=f"register_password_{form_key_suffix}")
        confirm_password = st.text_input("Confirm Password", type="password", key=f"confirm_password_{form_key_suffix}")
        
        if st.button("Create Account", key=f"create_account_btn_{form_key_suffix}"):
            logger.info(f"Account creation attempt for: {new_username}")
            # Validate inputs
            if not new_username or not new_password:
                logger.warning("Account creation failed: empty username or password")
                st.error("Username and password cannot be empty")
                return False
            
            if new_password != confirm_password:
                logger.warning("Account creation failed: passwords do not match")
                st.error("Passwords do not match")
                return False
            
            if new_username in users:
                logger.warning(f"Account creation failed: username '{new_username}' already exists")
                st.error("Username already exists. Please choose a different one.")
                return False
            
            # Create new user
            users[new_username] = hash_password(new_password)
            save_users(users)
            
            # Create folder structure for the new user
            if create_user_folder_structure(new_username):
                # Set success flag
                st.session_state.registration_success = True
                # Increment the form reset key to force form reset
                st.session_state.form_reset_key += 1
                logger.info(f"Account created successfully for user: {new_username}")
                st.success(f"Account created successfully! You can now login as {new_username}")
                # Force a rerun to reset all form fields
                st.experimental_rerun()
            else:
                logger.error(f"Failed to create folder structure for user: {new_username}")
                st.error("Error creating user folder structure")
    
    # Display a placeholder image
    try:
        placeholder_image_path = "image_place_holder.png"
        if os.path.exists(placeholder_image_path):
            from PIL import Image
            placeholder_img = Image.open(placeholder_image_path)
            placeholder_img = placeholder_img.resize((720, 480))
            st.image(placeholder_img, caption="VT Generator - Visual Transcription Service")
    except Exception as e:
        logger.error(f"Error displaying placeholder image: {e}")
        st.info("VT Generator - Visual Transcription Service")
    
    return False

def logout():
    """Log out the current user"""
    # Save current settings before logout if user is logged in
    if st.session_state.get("logged_in", False) and st.session_state.get("current_user"):
        username = st.session_state.current_user
        logger.info(f"Logging out user: {username}")
        
        settings = {
            "frame_increment": st.session_state.get("frame_increment", 1),
            "stroke_slider": st.session_state.get("stroke_slider", 3),
            "stroke_color": st.session_state.get("stroke_color", "#00FF00"),
            "max_words": st.session_state.get("max_words", "100"),
            "prompt_category": st.session_state.get("prompt_category", "general")
        }
        
        if save_user_settings(username, settings):
            logger.debug(f"Saved settings for user {username} during logout")
        else:
            logger.warning(f"Failed to save settings for user {username} during logout")
    
    # Reset login and project selection status
    if "logged_in" in st.session_state:
        st.session_state.logged_in = False
    if "current_user" in st.session_state:
        current_user = st.session_state.current_user
        st.session_state.current_user = None
        logger.info(f"User {current_user} logged out successfully")
    if "user_settings_loaded" in st.session_state:
        st.session_state.user_settings_loaded = False
    if "project_selected" in st.session_state:
        st.session_state.project_selected = False
    if "current_project" in st.session_state:
        st.session_state.current_project = None
    
    st.success("Logged out successfully")
    st.experimental_rerun() 