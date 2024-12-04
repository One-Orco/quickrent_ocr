import pytesseract
from app.utils.preprocessing import preprocess_image
from app.utils.beautify import beautify_extracted_text

# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
def perform_ocr(image_path: str, doc_type: str):
    preprocessing_modes = ["default", "binary", "adaptive", "blur"]
    extracted_texts = {}
    blur_text = ""

    for mode in preprocessing_modes:
        processed_image = preprocess_image(image_path, mode)
        extracted_text = pytesseract.image_to_string(processed_image, lang="ara+eng")
        extracted_texts[mode] = extracted_text
        if mode == "blur":
            blur_text = extracted_text

    # Combine all extracted text variations except blur with labels
    combined_text = "\n\n".join([f"[{mode.upper()} METHOD]\n{text}" for mode, text in extracted_texts.items()])

    # Beautify the extracted text based on the document type
    return beautify_extracted_text(combined_text, blur_text, doc_type)
