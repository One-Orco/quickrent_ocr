from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import re
import cv2
import numpy as np
import pytesseract
from typing import Dict, Union
from collections import Counter
from app.utils.ocr import preprocess_image, beautify_extracted_text
from app.utils.beautify import beautify_id_card,beautify_title_deed

router = APIRouter()

# Define the OCR endpoint
@router.post("/upload-document/")
async def upload_document(file: UploadFile = File(...), doc_type: str = "id_card") -> Dict:
    if file.content_type not in ["image/jpeg", "image/png", "image/tiff"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JPEG, PNG, or TIFF image.")

    try:
        # Save the uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(file.file.read())

        # Attempt multiple preprocessing methods for OCR accuracy
        preprocessing_modes = ["default", "binary", "adaptive", "blur"]
        extracted_texts = {}
        blur_text = ""

        for mode in preprocessing_modes:
            processed_image = preprocess_image(temp_file_path, mode)
            extracted_text = pytesseract.image_to_string(processed_image, lang="eng")
            extracted_texts[mode] = extracted_text
            if mode == "blur":
                blur_text = extracted_text

        combined_text = "\n\n".join([f"[{mode.upper()} METHOD]\n{text}" for mode, text in extracted_texts.items()])

        # Clean up temporary file
        os.remove(temp_file_path)

        beautified_text = beautify_extracted_text(combined_text, blur_text, doc_type)

        return beautified_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while processing the file: {str(e)}")

# Image preprocessing function to enhance OCR accuracy
def preprocess_image(image_path: str, mode: str = "default") -> np.ndarray:
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if mode == "binary":
        _, processed_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif mode == "adaptive":
        processed_image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    elif mode == "blur":
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, processed_image = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        processed_image = gray

    return processed_image




# Beautify extracted text based on document type
def beautify_extracted_text(text: str, blur_text: str, doc_type: str) -> Dict:
    if doc_type == "id_card":
        return beautify_id_card(text, blur_text)
    elif doc_type == "title_deed":
        return beautify_title_deed(text)
    else:
        return {"raw_text": text}


