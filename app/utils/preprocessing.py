import cv2
import numpy as np

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