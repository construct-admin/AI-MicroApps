"""
Media upload tab UI components for Visual Transcription app
"""
import streamlit as st
import os
import tempfile
import cv2
from file_handling import parse_srt

def render_media_tab():
    """Render the media upload tab."""
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