import requests
import cv2
from azure.ai.vision.imageanalysis.models import VisualFeatures
from pprint import pprint
import os
import base64


def analyze_image_Azure_Vision_Analysis(image_data, client, visual_features):
    """
    Sends an image to the Azure Image Analysis endpoint and returns the analysis result.
    
    Args:
        image_path (str): Path to the image file.
        endpoint_url (str): The full endpoint URL (e.g., "https://<your-region>.api.cognitive.microsoft.com/imageanalysis:analyze").
        subscription_key (str): Your subscription key for the service.
        
    Returns:
        dict: JSON response containing the analysis result.
    """
    print("visual_features = ", visual_features)

    # Convert the image (NumPy array) to bytes
    _, image_bytes = cv2.imencode('.jpg', image_data)
    image_data = image_bytes.tobytes()
    
    # visual_features_list = []

    # if "TAGS" in visual_features:
    #     visual_features_list.append(VisualFeatures.TAGS)

    # if "OBJECTS" in visual_features:
    #     visual_features_list.append(VisualFeatures.OBJECTS)

    # if "CAPTION" in visual_features:
    #     visual_features_list.append(VisualFeatures.CAPTION)
    
    # if "DENSE_CAPTIONS" in visual_features:
    #     visual_features_list.append(VisualFeatures.DENSE_CAPTIONS)

    # if "READ" in visual_features:
    #     visual_features_list.append(VisualFeatures.READ)

    # if "SMART_CROPS" in visual_features:
    #     visual_features_list.append(VisualFeatures.SMART_CROPS)

    # if "PEOPLE" in visual_features:
    #     visual_features_list.append(VisualFeatures.PEOPLE)

    visual_features =[ #TODO: Make this customizable
        VisualFeatures.TAGS,
        VisualFeatures.OBJECTS,
        VisualFeatures.CAPTION,
        VisualFeatures.DENSE_CAPTIONS,
        VisualFeatures.READ,
        VisualFeatures.SMART_CROPS,
        VisualFeatures.PEOPLE,
    ]


    result = client._analyze_from_image_data(
        image_data=image_data,
        visual_features=visual_features,
        gender_neutral_caption=False,
        language="en"
    )
    print("result = ", result)
    message = result["captionResult"]["text"]
    confidence = result["captionResult"]["confidence"]
    

    return {"message": message, "confidence": confidence}

    # Send the POST request with the image data.
    # response = requests.post(endpoint_url, headers=headers, params=params, data=image_data)
    
    # # Raise an exception if the request was not successful.
    # response.raise_for_status()
    
    # Return the JSON result.
    # return response.json()


def analyze_image_gpt4(image_data, prompt):
    """
    Sends an image (NumPy array) and a prompt to the Azure OpenAI API for analysis.

    Parameters:
    - image_data (numpy.ndarray): The image data from OpenCV.
    - prompt (str): The text prompt for the model.

    Returns:
    - dict: The JSON response from the API.
    """

    # Get environment variables
    url = os.getenv("Azure_OpenAI_Base_URL")  # Example: "https://your-resource-name.openai.azure.com"
    api_key = os.getenv("Azure_OpenAI_Key")


    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    # Convert the image (NumPy array) to base64-encoded JPEG
    try:
        _, buffer = cv2.imencode('.jpg', image_data)  # Convert numpy array to JPEG
        base64_image = base64.b64encode(buffer).decode("utf-8")  # Encode to Base64
    except Exception as e:
        return {"error": f"Failed to process image: {str(e)}"}

    # ✅ **Correcting `image_url` Structure** ✅
    image_payload = {"url": f"data:image/jpeg;base64,{base64_image}"}  # Now an object, not a string

    # Construct the payload
    payload = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant that analyzes images."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": image_payload}  # ✅ This is now an object
            ]}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }

    # Send the request
    response = requests.post(url, headers=headers, json=payload)

    # Debug response if error occurs
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")  # Print error for debugging
        return {"error": response.text, "status_code": response.status_code}

    pprint(response.json())
    return response.json()
