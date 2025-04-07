import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import base64
import requests
from PIL import Image
from openai import OpenAI
from docx import Document

# Initialize OpenAI client
GPT_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=GPT_API_KEY)

# Set Streamlit theme
st.set_page_config(page_title="VT Generator", page_icon="🖼️", layout="wide")

# Sidebar setup
st.sidebar.title("Saved Frames & Transcripts")
st.session_state.setdefault("saved_frames", [])
st.session_state.setdefault("saved_subtitles", [])
st.session_state.setdefault("frame_index", 0)
st.session_state.setdefault("frame_subtitle_map", {})
st.session_state.setdefault("subtitles", {})

# Upload Video and SRT File
video_file = st.file_uploader("Upload Video File (MP4)", type=["mp4"])
srt_file = st.file_uploader("Upload Subtitle File (SRT)", type=["srt"])

# Function to parse SRT files
def parse_srt(file):
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
    return subtitles

if video_file and srt_file and st.button("Process Video & Transcript"):
    temp_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    with open(temp_video_path, "wb") as f:
        f.write(video_file.read())

    st.session_state["subtitles"] = parse_srt(srt_file)
    cap = cv2.VideoCapture(temp_video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if not st.session_state.get("frames"):
        st.session_state["frames"] = [Image.fromarray(cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2RGB)) for _ in range(total_frames) if cap.read()[0]]

    cap.release()
    st.session_state["frame_subtitle_map"] = {int(start_time * fps): text for start_time, text in st.session_state["subtitles"].items()}

# Display transcript
st.sidebar.subheader("Transcript")
for timestamp, text in st.session_state["subtitles"].items():
    st.sidebar.write(f"**{timestamp}**: {text}")

# Frame Navigation
total_frames = len(st.session_state.get("frames", [])) - 1
if total_frames >= 0:
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

# Show saved frames
for i, (frame, subtitle) in enumerate(zip(st.session_state["saved_frames"], st.session_state["saved_subtitles"])):
    st.sidebar.image(frame, caption=f"Saved Frame {i}")
    st.sidebar.write(subtitle)

# Function to encode image as base64
def encode_image(image):
    buffered = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    image.save(buffered, format="JPEG")
    with open(buffered.name, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Transcription using OpenAI's API
if "transcriptions" not in st.session_state:
    st.session_state["transcriptions"] = {}

for i, (frame, subtitle) in enumerate(zip(st.session_state["saved_frames"], st.session_state["saved_subtitles"])):
    if st.sidebar.button(f"Transcribe Frame {i}"):
        st.sidebar.write(f"Processing transcription for Frame {i}...")
        base64_image = encode_image(frame)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GPT_API_KEY}"}
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": "What’s in this image?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            "max_tokens": 300
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        gpt_response = response.json()
        transcription = gpt_response['choices'][0]['message']['content']
        st.sidebar.text_area(f"GPT Response for Frame {i}", transcription)
        
        st.session_state["transcriptions"][i] = transcription
        
    if i in st.session_state["transcriptions"]:
        if st.sidebar.button(f"Insert into Transcript {i}"):
            frame_timestamp = list(st.session_state["subtitles"].keys())[i]
            st.session_state["subtitles"][frame_timestamp] += f"\n[GPT]: {st.session_state['transcriptions'][i]}"
            st.sidebar.write("Inserted into transcript!")

# Download full transcript
def download_transcript():
    doc = Document()
    doc.add_heading("Visual Transcript", level=1)
    for timestamp, text in st.session_state["subtitles"].items():
        doc.add_paragraph(f"{timestamp}: {text}")
    temp_doc_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
    doc.save(temp_doc_path)
    with open(temp_doc_path, "rb") as doc_file:
        st.sidebar.download_button("Download Transcript", doc_file, file_name="visual_transcript.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

st.sidebar.subheader("Download Options")
download_transcript()
