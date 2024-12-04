from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.file_handler import handle_uploaded_file, delete_temp_file
from app.utils.ocr import perform_ocr

router = APIRouter()


@app.post("/upload-document/")
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
            # Store the blur mode text separately
            if mode == "blur":
                blur_text = extracted_text

        # Combine all extracted text variations except blur with labels
        combined_text = "\n\n".join([f"[{mode.upper()} METHOD]\n{text}" for mode, text in extracted_texts.items()])

        # Remove the temporary file after processing
        os.remove(temp_file_path)

        # Beautify the extracted text based on the document type
        beautified_text = beautify_extracted_text(combined_text, blur_text, doc_type)

        # Return the beautified text in JSON format
        return beautified_text

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while processing the file: {str(e)}")
