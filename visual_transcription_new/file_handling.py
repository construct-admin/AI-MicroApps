"""
File handling utilities for Visual Transcription app
"""
import os
import tempfile
import json
import re
import streamlit as st
from docx import Document
from image_processing import seconds_to_timestamp

def parse_srt(file):
    """Parse SRT subtitle file and return a dictionary of timestamps and text."""
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

def download_transcript(merge_transcripts_func):
    """Generate and provide a download button for transcript document."""
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
            merged_transcripts = merge_transcripts_func()
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
                        st.download_button(
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

def load_settings():
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