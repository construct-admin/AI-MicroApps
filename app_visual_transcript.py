import streamlit as st
import cv2
import tempfile
import os
from visual_transcription.src.api_calls import analyze_image_Azure_Vision_Analysis, analyze_image_gpt4  # Your custom function to call the API
from visual_transcription.utils.initialise_LLM_models import Azure_Vision_analyse_dict
from visual_transcription.utils.utilities import get_frame_timestamp, image_to_base64, insert_VT_into_AT
import json

# -----------------------------------------------
# Initialise some of the session_state values
# -----------------------------------------------

if "Azure Vision Add Captions" not in st.session_state:
    st.session_state["Azure Vision Add Captions"] = Azure_Vision_analyse_dict #TODO: Make more efficient - only one if statement required


if "gpt-4o" not in st.session_state:
    with open(r"visual_transcription\utils\chat_GPT.json", "r") as json_file:
        gpt4o_into = json.load(json_file)
        st.session_state['gpt-4o'] = {"prompt": gpt4o_into["prompt"], "max_words": gpt4o_into["max_words"]}
        st.session_state['gpt-4o']["prompt"] = st.session_state['gpt-4o']["prompt"].replace("%MAX_WORDS%", gpt4o_into["max_words"])



if "saved_frames" not in st.session_state:
    st.session_state.saved_frames = dict()
if 'video' not in st.session_state:
    st.session_state.video = None
if 'frame_number' not in st.session_state:
    st.session_state.frame_number = 0
if 'total_frames' not in st.session_state:
    st.session_state.total_frames = 0
if 'uploaded' not in st.session_state:
    st.session_state.uploaded = False
if 'uploaded_transcript_objects' not in st.session_state:
    st.session_state.uploaded_transcript_objects = dict()
if "audio_transcript" not in st.session_state:
    st.session_state.audio_transcript = []

st.title('Video Transcription Service')

if st.session_state.audio_transcript == []:
    uploaded_json = st.file_uploader('Drag and drop an audio transcript file here', type=['json'])
    if uploaded_json is not None:
        st.session_state.audio_transcript = json.load(uploaded_json)

# -----------------------------------------------
# Model Selection
# -----------------------------------------------
model_options = ['Azure Vision Add Captions', 'gpt-4o', 'Model C']
selected_model = st.selectbox('Select a model for visual transcription', model_options)
st.session_state['selected_model'] = selected_model


# -----------------------------------------------
# Display informaiton that is relevant to the selected_model
# -----------------------------------------------
if st.session_state['selected_model'] == "Azure Vision Add Captions":
    visual_features_model_options = ["TAGS", "OBJECTS", "CAPTION", "DENSE_CAPTIONS", "READ", "SMART_CROPS", "PEOPLE"]
    visual_features = st.multiselect('Select the visual aspects that the model should transcribe', visual_features_model_options)
    st.session_state['Azure Vision Add Captions']["visual_features"] = visual_features

if st.session_state['selected_model'] == "gpt-4o":

    filter_options = ["hate", "protected_material_code", "protected_material_text", "self_harm", "sexual", "violence"]
    selected_filters = st.multiselect('Select filters', filter_options)
    print("selected_filters = ", selected_filters)
    st.session_state['gpt-4o']["selected_filters"] = selected_filters

    if "hate" in selected_filters:
        severity_options = ["safe"]
        chosen_severity = "safe"
        # chosen_severity = st.selectbox('select the filter severity for hate', severity_options)
        st.session_state["gpt-4o"]["hate"] = chosen_severity

    if "protected_material_code" in selected_filters:
        severity_options = ["safe"]
        chosen_severity = "safe"
        # chosen_severity = st.selectbox('select the filter severity for protected_material_code', severity_options)
        st.session_state["gpt-4o"]["protected_material_code"] = chosen_severity

    if "protected_material_text" in selected_filters:
        severity_options = ["safe"]
        chosen_severity = "safe"
        # chosen_severity = st.selectbox('select the filter severity for protected_material_text', severity_options)
        st.session_state["gpt-4o"]["protected_material_text"] = chosen_severity

    if "self_harm" in selected_filters:
        severity_options = ["safe"]
        chosen_severity = "safe"
        # chosen_severity = st.selectbox('select the filter severity for self harm', severity_options)
        st.session_state["gpt-4o"]["self_harm"] = chosen_severity

    if "sexual" in selected_filters:
        severity_options = ["safe"]
        chosen_severity = "safe"
        # chosen_severity = st.selectbox('select the filter severity for sexsual', severity_options)
        st.session_state["gpt-4o"]["sexual"] = chosen_severity

    if "violence" in selected_filters:
        severity_options = ["safe"]
        chosen_severity = st.selectbox('select the filter severity for violence', severity_options)
        st.session_state["gpt-4o"]["violence"] = chosen_severity

    max_words = str(st.text_input(label="Please select the maximum number of words that the VT may be", value=st.session_state['gpt-4o']["max_words"]))

    st.session_state['gpt-4o']["prompt"] = st.session_state['gpt-4o']["prompt"].replace(st.session_state['gpt-4o']["max_words"], max_words)
    st.session_state['gpt-4o']["max_words"] = max_words

    # prompt = st.session_state['gpt-4o']["prompt"].replace(r"{max_words}", st.session_state['gpt-4o']["max_words"])
    prompt = st.session_state['gpt-4o']["prompt"]
    st.session_state['gpt-4o']["prompt"] = st.text_area(label="prompt", value=prompt)


# -----------------------------------------------
# File Uploader: Drag and Drop a Video File
# -----------------------------------------------
if not st.session_state.uploaded:
    uploaded_file = st.file_uploader('Drag and drop a video file here', type=['mp4', 'avi', 'mov'])
else:
    uploaded_file = None

if uploaded_file is not None:
    if not st.session_state.uploaded:
        st.success('Video uploaded successfully! Processing transcription...')
        # Save the uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        st.write(f'Temporary file path: {temp_file_path}')
        if not os.path.exists(temp_file_path):
            st.error('Temporary file was not created successfully.')
        else:
            st.session_state.video = cv2.VideoCapture(temp_file_path)
            if st.session_state.video.isOpened():
                st.session_state.total_frames = int(st.session_state.video.get(cv2.CAP_PROP_FRAME_COUNT))
                st.session_state.uploaded = True
            else:
                st.error('Could not open video file.')

# -----------------------------------------------
# Display Video Frames and Controls
# -----------------------------------------------
if st.session_state.uploaded:
    # Use a slider to select the frame number
    frame_number = st.slider('Select frame', 0, st.session_state.total_frames - 1, st.session_state.frame_number)
    st.session_state.frame_number = frame_number
    st.write(f"frame_number: {st.session_state.frame_number}")

    stframe = st.empty()
    st.session_state.video.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
    ret, frame = st.session_state.video.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        stframe.image(frame_rgb, channels='RGB')
    else:
        st.error('Could not read the frame.')

# Navigation and Save Frame buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button('Move Left'):
        if st.session_state.frame_number > 0:
            st.session_state.frame_number -= 1
with col2:
    if st.button('Save Frame Index'):
        # Ensure we capture the correct frame
        st.session_state.video.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
        ret, frame = st.session_state.video.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.session_state.saved_frames[st.session_state.frame_number] = {
                'frame': frame_rgb,
                'has_visual_transcripts': False,
                'getting_visual_transcripts': False,
                'visual_transcripts': None
            }
            st.write(f'Saved frame index: {st.session_state.frame_number}')
        else:
            st.error('Could not capture the frame to save.')
with col3:
    if st.button('Move Right'):
        if st.session_state.frame_number < st.session_state.total_frames - 1:
            st.session_state.frame_number += 1

# -----------------------------------------------
# Sidebar: Display Saved Frames as Clickable Cards (using st.button)
# -----------------------------------------------
with st.sidebar:
    st.markdown("### Selected Frames")
    for frame_index, frame_info in sorted(st.session_state.saved_frames.items()):
        base64_img = image_to_base64(frame_info['frame'])
        transcript_text = frame_info['visual_transcripts'] if frame_info['visual_transcripts'] else 'No transcript yet'
        
        # Display the card using Markdown for styling
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                <h4>Frame {frame_index}</h4>
                <img src="data:image/jpeg;base64,{base64_img}" style="width:100%;" />
                <p>{transcript_text}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Create a button below each card
        if not frame_info['has_visual_transcripts']:
            if st.button(f"Transcribe frame {frame_index}", key=f"btn_{frame_index}"):

                if st.session_state['selected_model'] == "Azure Vision Add Captions":
                    response = analyze_image_Azure_Vision_Analysis(frame_info['frame'], st.session_state[st.session_state['selected_model']]['client'], st.session_state['Azure Vision Add Captions']["visual_features"])
                    message = response["message"]


                elif st.session_state['selected_model'] == "gpt-4o":
                    response = analyze_image_gpt4(frame_info['frame'], st.session_state["gpt-4o"]["prompt"])
                    choices = response["choices"]
                    message = choices[0]["message"]["content"]

                # elif st.session_state['selected_model'] == "new model":
                #     response = MODEL_FUNCTION(INPUTS)
                #     choices = response["choices"]
                #     message = choices[0]["message"]["content"]

                else:
                    raise ValueError("Invalid model selected")

                print("This is the session state: ", st.session_state['selected_model'])

                st.session_state.saved_frames[frame_index]['visual_transcripts'] = message
                st.session_state.saved_frames[frame_index]['has_visual_transcripts'] = True
                st.session_state.saved_frames[frame_index]['time_stamp'] = get_frame_timestamp(frame_index, st.session_state.video)
                st.success("Visual transcriptions updated for frame nr: " + str(frame_index) + ".")

        # Button to add a frame to the transcript objects
        elif st.button(f"Add frame {frame_index} to transcript", key=f"add_{frame_index}"):
            st.session_state.uploaded_transcript_objects[frame_index] = st.session_state.saved_frames[frame_index]
            del st.session_state.saved_frames[frame_index]
            st.success("Frame " + str(frame_index) + " added to transcript objects.")

# -----------------------------------------------
# Sidebar: Display Uploaded Transcript Messages via a Select Slider
# -----------------------------------------------
with st.sidebar:
    st.markdown("### Uploaded Transcript Messages")

    st.session_state.audio_transcript

    if st.session_state.uploaded_transcript_objects:
        
        for frame_index, frame_info in sorted(st.session_state.uploaded_transcript_objects.items()):
            st.write(frame_info['visual_transcripts'], frame_info['time_stamp'])
            insert_VT_into_AT(frame_info)

            # Use a select slider (which allows discrete options) to choose a frame from the uploaded transcripts
            transcript_message = st.session_state.uploaded_transcript_objects[frame_index]['visual_transcripts']
        st.write("Transcript message:", transcript_message)
    else:
        st.write("No uploaded transcript objects yet.")

# -----------------------------------------------
# Sidebar: Refresh Button
# -----------------------------------------------
# with st.sidebar:
#     if st.button('Refresh'):
#         st.success('Reloaded')

# -----------------------------------------------
# Add Some Spacing at the Bottom
# -----------------------------------------------
st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

# Optionally, you can release the video capture object on app exit
# if st.session_state.video is not None:
#     st.session_state.video.release()
