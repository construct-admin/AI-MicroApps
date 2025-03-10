import cv2
from io import BytesIO
import base64
import streamlit as st
def get_frame_timestamp(frame_index, video_capture):
    """
    Given a frame index and a cv2.VideoCapture object, this function calculates
    the corresponding timestamp in the video and returns it as a formatted string (HH:MM:SS.ss).

    Parameters:
        frame_index (int): The index of the frame.
        video_capture (cv2.VideoCapture): The OpenCV VideoCapture object for the video.

    Returns:
        str: The timestamp for the frame in the format "HH:MM:SS.ss".
    """
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        return "00:00:00.00"
    
    # Calculate seconds from frame index
    seconds = frame_index / fps
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    # Format timestamp as HH:MM:SS.ss
    return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"

# -----------------------------------------------
# Helper Function: Convert a NumPy image to Base64
# -----------------------------------------------
def image_to_base64(image):
    buffered = BytesIO()
    from PIL import Image
    pil_image = Image.fromarray(image)
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()



# -----------------------------------------------
# Set Up the Streamlit App
# -----------------------------------------------

def insert_VT_into_AT(frame_info, ):

    VT_time_stamp = frame_info["time_stamp"]
    VT_transcripts = frame_info["visual_transcripts"]

    st.session_state.audio_transcript.append({"time_stamp": VT_time_stamp, "transcripts": VT_transcripts, "mode": "VT"})
    st.session_state.audio_transcript.sort(key=lambda x: x["time_stamp"])