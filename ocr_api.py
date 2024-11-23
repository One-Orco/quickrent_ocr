from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
import tempfile
import shutil
import os

app = FastAPI()

@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        # Create a temporary file to store the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            # Copy the uploaded file's content to the temporary file
            shutil.copyfileobj(file.file, tmp)
            temp_file_path = tmp.name

        # Open the image using Pillow
        img = Image.open(temp_file_path)

        # Perform OCR using pytesseract
        raw_text = pytesseract.image_to_string(img)

        # Delete the temporary file after processing
        os.remove(temp_file_path)

        # Return the extracted text as JSON
        return JSONResponse(content={"text": raw_text})
    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(content={"error": str(e)}, status_code=500)

