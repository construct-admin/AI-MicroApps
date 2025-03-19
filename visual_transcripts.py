import streamlit as st
import numpy as np
import os
import tempfile
import base64
import requests
from PIL import Image
from openai import OpenAI
from docx import Document
import cv2  # Ensure OpenCV is installed

# ✅ OpenAI API Key
GPT_API_KEY = os.getenv("OPENAI_API_KEY")
if not GPT_API_KEY:
    st.error("⚠️ OpenAI API Key is missing! Add it in Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=GPT_API_KEY)

# ✅ Set Streamlit Page Config
st.set_page_config(page_title="VT Generator", page_icon="🖼️", layout="wide")

# ✅ Debugging Log
if "debug_log" not in st.session_state:
    st.session_state["debug_log"] = []

# ✅ Ensure all session state variables exist
session_defaults = {
    "saved_frames": [],
    "saved_subtitles": [],
    "frame_index": 0,
    "frame_subtitle_map": {},
    "subtitles": {},
    "frames": [],
    "transcriptions": {},
    "video_processed": False
}
for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ✅ Debugging Step 1: Check Session State Initialization
st.sidebar.write("✅ Debug Log")
st.session_state["debug_log"].append("Session state initialized.")
st.sidebar.text_area("Debug Log", "\n".join(st.session_state["debug_log"]), height=200)

# ✅ File Uploads
video_file = st.file_uploader("Upload Video File (MP4)", type=["mp4"])
srt_file = st.file_uploader("Upload Subtitle File (SRT)", type=["srt"])

# ✅ Debugging Step 2: Check File Uploads
if video_file:
    st.session_state["debug_log"].append("✅ Video file uploaded.")
if srt_file:
    st.session_state["debug_log"].append("✅ SRT file uploaded.")
st.sidebar.text_area("Debug Log", "\n".join(st.session_state["debug_log"]), height=200)

# ✅ Function to parse SRT files
def parse_srt(file):
    subtitles = {}
    try:
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
    except Exception as e:
        st.error(f"❌ Error parsing SRT file: {e}")
        st.session_state["debug_log"].append(f"❌ SRT Parsing Error: {e}")
    return subtitles

# ✅ Function to extract frames from video
def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.error("❌ Failed to open video file.")
        st.session_state["debug_log"].append("❌ OpenCV failed to open video file.")
        return [], 0

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []

    for i in range(total_frames):
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame))
        if i % 100 == 0:
            st.session_state["debug_log"].append(f"✅ Extracted {i}/{total_frames} frames...")

    cap.release()
    return frames, fps

# ✅ Process Video and Transcript
if video_file and srt_file and st.button("Process Video & Transcript"):
    st.session_state["debug_log"].append("🚀 Processing started.")
    try:
        temp_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        with open(temp_video_path, "wb") as f:
            f.write(video_file.read())

        subtitles = parse_srt(srt_file)
        frames, fps = extract_frames(temp_video_path)

        if frames:
            st.session_state["frames"] = frames
            st.session_state["subtitles"] = subtitles
            st.session_state["frame_subtitle_map"] = {
                int(start_time * fps): text for start_time, text in subtitles.items()
            }
            st.session_state["frame_index"] = 0  # Reset frame index
            st.session_state["video_processed"] = True  # ✅ Track processing state
            st.session_state["debug_log"].append("✅ Video & transcript processing complete!")
            st.success("✅ Video and transcript processed successfully!")
        else:
            st.error("❌ Failed to extract frames. Check your video file.")
            st.session_state["debug_log"].append("❌ Frame extraction failed.")
    except Exception as e:
        st.error(f"❌ Error processing video: {e}")
        st.session_state["debug_log"].append(f"❌ Video Processing Error: {e}")

st.sidebar.text_area("Debug Log", "\n".join(st.session_state["debug_log"]), height=200)

# ✅ Display transcript
st.sidebar.subheader("Transcript")
if st.session_state["video_processed"]:
    for timestamp, text in st.session_state["subtitles"].items():
        st.sidebar.write(f"**{timestamp}**: {text}")

# ✅ Frame Navigation
total_frames = len(st.session_state["frames"]) - 1
if total_frames >= 0 and st.session_state["video_processed"]:
    frame_index = st.slider("Select Frame", 0, total_frames, st.session_state["frame_index"], key="frame_slider")
    st.session_state["frame_index"] = frame_index
    st.image(st.session_state["frames"][frame_index], caption=f"Frame {frame_index}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous Frame"):
            st.session_state["frame_index"] = max(0, frame_index - 1)
    with col2:
        if st.button("Next Frame"):
            st.session_state["frame_index"] = min(total_frames, frame_index + 1)

    if st.button("Save Index"):
        st.session_state["saved_frames"].append(st.session_state["frames"][frame_index])
        st.session_state["saved_subtitles"].append(st.session_state["frame_subtitle_map"].get(frame_index, "No Subtitle"))

st.sidebar.text_area("Debug Log", "\n".join(st.session_state["debug_log"]), height=200)
