from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.file_handler import handle_uploaded_file, delete_temp_file
from app.utils.ocr import perform_ocr

router = APIRouter()


@router.post("/upload-document/")
async def upload_document(file: UploadFile = File(...), doc_type: str = "id_card"):
    if file.content_type not in ["image/jpeg", "image/png", "image/tiff"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JPEG, PNG, or TIFF image.")

    try:
        temp_file_path = handle_uploaded_file(file)

        # Perform OCR and return the beautified JSON response
        beautified_text = perform_ocr(temp_file_path, doc_type)

        # Remove temporary file
        delete_temp_file(temp_file_path)

        return beautified_text

    except Exception as e:
        delete_temp_file(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error occurred while processing the file: {str(e)}")
