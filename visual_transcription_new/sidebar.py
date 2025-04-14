"""
Sidebar UI components for Visual Transcription app
"""
import streamlit as st
from PIL import Image
import os
import cv2

from image_processing import image_to_base64, encode_image
from file_handling import download_transcript

def render_sidebar(openai_client, merge_transcripts_func):
    """Render the application sidebar."""
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
                                
                                # Get OpenAI API key
                                api_key = os.getenv("PERSONAL_OPENAI_KEY")
                                
                                # Show max tokens information
                                max_tokens = int(st.session_state["max_words"]) * 4
                                
                                # Make API call
                                response = openai_client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "user", "content": [
                                            {"type": "text", "text": prompt_text},
                                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                        ]}
                                    ],
                                    max_tokens=max_tokens
                                )
                                
                                transcription = response.choices[0].message.content

                                # Update session state
                                st.session_state.saved_frames[frame_number]['visual_transcripts'] = transcription
                                st.session_state.saved_frames[frame_number]['has_visual_transcripts'] = True
                                st.session_state["transcriptions"][frame_number] = transcription
                                
                                # Get timestamp if needed
                                if st.session_state.get('video') and st.session_state.get('video').isOpened():
                                    try:
                                        video_obj = st.session_state.video
                                        from image_processing import get_frame_timestamp
                                        st.session_state.saved_frames[frame_number]['time_stamp'] = get_frame_timestamp(frame_number, video_obj)
                                    except Exception as ts_error:
                                        st.warning(f"Could not get timestamp for Frame {frame_number}: {ts_error}")
                                        st.session_state.saved_frames[frame_number]['time_stamp'] = "N/A"

                                st.success(f"Transcription completed for Frame {frame_number}.")
                                st.experimental_rerun()  # Update sidebar display
                            except Exception as api_error:
                                st.error(f"Transcription failed: {api_error}")

                with col2_side:
                    # Insert/Remove from Transcript Button
                    if frame_info.get('has_visual_transcripts', False):
                        # Check if transcription is already inserted
                        is_inserted = frame_number in st.session_state.get("inserted_transcriptions", set())
                        
                        # Change button text based on current state
                        button_text = f"Remove from Transcript #{frame_number}" if is_inserted else f"Insert to Transcript #{frame_number}"
                        button_key = f"toggle_{frame_number}"
                        
                        if st.button(button_text, key=button_key):
                            if is_inserted:
                                # REMOVE FROM TRANSCRIPT LOGIC
                                try:
                                    # Remove from inserted_transcriptions set
                                    st.session_state.inserted_transcriptions.remove(frame_number)
                                    
                                    # If this frame has a corresponding subtitle entry, clean up the GPT part
                                    if frame_number in st.session_state.get("frame_subtitle_map", {}):
                                        # Find the subtitle key
                                        subtitle_key = None
                                        for start_time, text in st.session_state.get("subtitles", {}).items():
                                            if int(start_time * int(st.session_state.video.get(cv2.CAP_PROP_FPS))) == frame_number:
                                                subtitle_key = start_time
                                                break
                                        
                                        if subtitle_key is not None and "\n[GPT]:" in st.session_state["subtitles"][subtitle_key]:
                                            # Remove only the GPT part
                                            original_text = st.session_state["subtitles"][subtitle_key].split("\n[GPT]:")[0]
                                            st.session_state["subtitles"][subtitle_key] = original_text
                                    
                                    st.success(f"Removed Frame {frame_number} from transcript.")
                                    st.experimental_rerun()
                                except Exception as remove_err:
                                    st.error(f"Error removing from transcript: {remove_err}")
                            else:
                                # INSERT INTO TRANSCRIPT LOGIC
                                try:
                                    # When a visual transcript is inserted:
                                    # 1. It's added to the existing subtitle text (if matching frame exists)
                                    # 2. The frame number is added to inserted_transcriptions set
                                    # 3. The merge_transcripts() function will include it in the combined chronological display
                                    
                                    # Insert into the subtitles dictionary
                                    if frame_number in st.session_state.get("frame_subtitle_map", {}):
                                        # Get existing subtitle text
                                        subtitle_key = None
                                        for start_time, text in st.session_state.get("subtitles", {}).items():
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
                            if frame_number in st.session_state.get("inserted_transcriptions", set()):
                                st.session_state.inserted_transcriptions.remove(frame_number)
                            
                            # Remove from transcriptions dictionary
                            if frame_number in st.session_state.get("transcriptions", {}):
                                del st.session_state.transcriptions[frame_number]
                                
                            # If this frame has a corresponding subtitle entry, clean up the GPT part
                            if frame_number in st.session_state.get("frame_subtitle_map", {}):
                                # Find the subtitle key
                                subtitle_key = None
                                for start_time, text in st.session_state.get("subtitles", {}).items():
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
        download_transcript(merge_transcripts_func) 