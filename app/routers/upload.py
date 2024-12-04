from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Literal
import os
import pytesseract
from app.utils.ocr import beautify_extracted_text
from app.utils.preprocessing import preprocess_image

router = APIRouter()

@router.post(
    "/upload-document/",
    summary="Upload and Process a Document for OCR",
    description="""
This endpoint allows you to upload an image of a document and process it using OCR. 
It supports both Arabic and English text recognition, applies multiple preprocessing 
techniques, and returns structured and beautified data depending on the document type.

### Supported `doc_type` Values:
- `id_card`: For processing ID cards.
- `title_deed`: For processing title deeds.
""",
    response_description="Structured data extracted from the uploaded document."
)
async def upload_document(
    file: UploadFile = File(..., description="The image file to process (JPEG, PNG, or TIFF)."),
    doc_type: Literal["id_card", "title_deed"] = "id_card"  # Restrict valid values
) -> Dict:
    """
    Upload an image document for OCR processing.

    Parameters:
    - file: The document image to be processed (JPEG, PNG, TIFF).
    - doc_type: The type of document being uploaded. Valid values:
        - `id_card`: For ID cards.
        - `title_deed`: For title deeds.

    Returns:
    A structured dictionary containing the extracted and beautified data.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/tiff"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a JPEG, PNG, or TIFF image."
        )

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
            extracted_text = pytesseract.image_to_string(processed_image, lang="ara+eng")
            extracted_texts[mode] = extracted_text
            if mode == "blur":
                blur_text = extracted_text

        combined_text = "\n\n".join([f"[{mode.upper()} METHOD]\n{text}" for mode, text in extracted_texts.items()])

        # Clean up temporary file
        os.remove(temp_file_path)

        beautified_text = beautify_extracted_text(combined_text, blur_text, doc_type)

        return beautified_text

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while processing the file: {str(e)}"
        )
