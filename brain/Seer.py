import google.generativeai as genai
from typing import Optional, Union, List
import os
import io
import base64
from PIL import Image
import numpy as np
import cv2
import easyocr  # EasyOCR replaces Tesseract here
import unicodedata

def set_personality(model_name: str) -> genai.GenerativeModel:
    """
    Configures the Seer AI model to interpret and act on requests
    related to Python library management. Returns a model instance
    that operates as 'Tai', with the sole purpose of generating shell
    commands or Python code to install or manage libraries.
    """
    return genai.GenerativeModel(
        model_name,
        system_instruction=(f"""
You are 'Tai', an AI configuration focused on highly capable at image understanding. Perform OCR, object detection, 
scene description, facial analysis, image classification, and multimodal reasoning. Return structured JSON 
with keys: description, objects, ocr_text, emotions, suggestions.
Do not include explanations or comments. Only output the required json.
If given a large JSON file with edit instructions, return the exact file with only those edits. 
If no edits are requested, return the file unchanged. 
Ensure all keys in the JSON files use double quotes.
        """)
    )

def generate_content(model: genai.GenerativeModel, prompt: str, get_content: Optional[bool] = False) -> Union[str, genai.types.GenerateContentResponse]:
    """
    Generates content from the AI model using a prompt.

    - Cleans formatting by removing code block markers.
    - Ensures the output is valid JSON, starting with a '['.
    """
    content = model.generate_content(prompt)
    text = content.text.strip()

    if text.startswith("```json"):
        text = text[9:].lstrip()
    if text.endswith("```"):
        text = text[:-3].rstrip()
    if not text.startswith("["):
        text = "[" + text

    return content if get_content else text

def process_image_bytes(seer_model: genai.GenerativeModel, image_bytes: bytes) -> dict:
    """
    Perform multi-stage image analysis: OCR, object detection, scene description, emotion analysis.

    Returns structured JSON.
    """
    # Decode image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    np_img = np.array(image)

    # OCR using EasyOCR
    reader = easyocr.Reader(['en'])  # You can specify other languages here
    ocr_results = reader.readtext(np_img)
    ocr_text = " ".join([result[1] for result in ocr_results])  # Join all the detected text

    # Basic object detection via OpenCV Haar cascades (face detection)
    gray = cv2.cvtColor(np_img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4).tolist()

    # Generate vision-model structured analysis
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    prompt = {
        'image_base64': encoded,
        'features': ['description', 'objects', 'emotions', 'suggestions']
    }
    response = seer_model.generate_content(prompt)
    vision_data = response.json()

    # Merge low-level and high-level
    vision_data['ocr_text'] = ocr_text.strip()
    vision_data['faces_detected'] = faces
    print(vision_data)
    return vision_data


def safe_unicode(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")