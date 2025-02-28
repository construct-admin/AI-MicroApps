import base64
import requests
import os
import dotenv
from pprint import pprint

dotenv.load_dotenv()

def send_image_to_azure_openai(deployment_name, image_path, prompt):
    """
    Sends an image and a prompt to the Azure OpenAI API for analysis.

    Parameters:
    - api_key (str): Your Azure OpenAI API key.
    - endpoint (str): Your Azure OpenAI service endpoint.
    - deployment_name (str): The name of your deployed model.
    - image_path (str): Path to the image file.
    - prompt (str): The text prompt for the model.

    Returns:
    - dict: The JSON response from the API.
    """

    url = os.getenv("Azure_OpenAI_Base_URL")

    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv("Azure_OpenAI_Key")
    }

    # Encode the image in base64 format
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {
        "messages": [
            {"role": "system", "content": "You are an AI assistant that analyzes images."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text, "status_code": response.status_code}

# Example Usage:
# Replace these values with your actual credentials and image path
DEPLOYMENT_NAME = "gpt-4o"

image_path = "image.png"
prompt = "Describe the contents of this image."

response = send_image_to_azure_openai(image_path, prompt)
pprint(response)