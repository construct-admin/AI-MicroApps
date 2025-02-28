from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
import streamlit as st
import os
import dotenv

dotenv.load_dotenv()

Azure_Vision_analyse_dict = {
    "region": "eastus",
    "client": ImageAnalysisClient(
        endpoint="https://rnd-calivision.cognitiveservices.azure.com/",
        credential=AzureKeyCredential(os.getenv("PERSONAL_AZURE_VISION_KEY"))
    ),
    "visual_features": None
}

