import re
from typing import Dict, Union
from collections import Counter

def beautify_id_card(text: str, blur_text: str) -> Dict[str, Union[str, Dict[str, str]]]:
    id_card_data = {
        "country": "",
        "authority": "",
        "card_type": "",
        "details": {
            "name": "",
            "date_of_birth": "",
            "issuing_date": "",
            "expiry_date": "",
            "nationality": "",
            "id_number": "",
            "sex": ""
        }
    }

    # Preprocessing: Clean up text by replacing unwanted characters and normalizing
    clean_text = re.sub(r'[^a-zA-Z0-9/\n\s:-]', '', text)  # Remove unwanted characters
    clean_text = re.sub(r' +', ' ', clean_text)  # Replace multiple spaces with a single space

    # Debugging: Save cleaned text for inspection
    with open("ocr_output_cleaned_debug.txt", "w") as debug_file:
        debug_file.write(clean_text)

    lines = clean_text.splitlines()

    # Collect potential name and nationality variations
    name_variations = []
    nationality_variations = []

    # Using heuristic to find details
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Country and authority detection
        if "united arab emirates" in line_lower:
            id_card_data["country"] = "United Arab Emirates"
        elif "federal authority" in line_lower:
            id_card_data["authority"] = "Federal Authority for Identity & Citizenship, Customs & Port Security"

        # Card type detection
        if "golden card" in line_lower:
            id_card_data["card_type"] = "Golden Card"

        # Name detection - collect all variations
        if "name:" in line_lower:
            name_raw = re.sub(r'name[:\s]*', '', line, flags=re.IGNORECASE).strip()
            if name_raw:
                name_variations.append(name_raw)

        # Date of birth detection
        if "date of birth" in line_lower:
            dob_match = re.search(r'\d{2}/\d{2}/\d{4}', line)
            if dob_match:
                id_card_data["details"]["date_of_birth"] = dob_match.group(0)

        # Issuing date detection
        if "issuing" in line_lower or "issue date" in line_lower:
            issue_date_match = re.search(r'\d{2}/\d{2}/\d{4}', line)
            if issue_date_match:
                id_card_data["details"]["issuing_date"] = issue_date_match.group(0)
            elif i + 1 < len(lines):  # Check the next line if date is split
                next_line = lines[i + 1]
                issue_date_match_next = re.search(r'\d{2}/\d{2}/\d{4}', next_line)
                if issue_date_match_next:
                    id_card_data["details"]["issuing_date"] = issue_date_match_next.group(0)

        # Expiry date detection
        if any(keyword in line_lower for keyword in ["expiry", "exp", "valid until", "expire"]):
            expiry_date_match = re.search(r'\d{2}/\d{2}/\d{4}', line)
            if expiry_date_match:
                id_card_data["details"]["expiry_date"] = expiry_date_match.group(0)
            elif i + 1 < len(lines):  # Check the next lines if date is split
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j]
                        expiry_date_match_next = re.search(r'\d{2}/\d{2}/\d{4}', next_line)
                        if expiry_date_match_next:
                            id_card_data["details"]["expiry_date"] = expiry_date_match_next.group(0)
                            break

        # Nationality detection with variations
        if "nationality" in line_lower:
            nationality_match = re.sub(r'nationality[:\s]*', '', line, flags=re.IGNORECASE).strip()
            if nationality_match:
                nationality_variations.append(nationality_match.title())

        # Sex detection
        if "sex" in line_lower:
            sex_match = re.search(r'\b(m|male|f|female)\b', line_lower, re.IGNORECASE)
            if sex_match:
                id_card_data["details"]["sex"] = "M" if sex_match.group(0).lower() in ["m", "male"] else "F"

    # Determine the best name from collected variations
    if name_variations:
        id_card_data["details"]["name"] = get_best_name_variation(name_variations)

    # Determine the best nationality value based on a simple heuristic
    if nationality_variations:
        valid_country_names = ["Iraq", "United Arab Emirates", "India", "USA", "Canada", "Germany"]
        for nationality in nationality_variations:
            if nationality in valid_country_names:
                id_card_data["details"]["nationality"] = nationality
                break
        else:
            id_card_data["details"]["nationality"] = nationality_variations[0]

    # Extract ID number specifically from blur mode output
    blur_lines = blur_text.splitlines()
    for i, line in enumerate(blur_lines):
        if line.count('-') == 3:
            id_number_match = re.search(r'(\d{1,4}-\d{1,4}-\d{1,7}-\d+)', line)
            if id_number_match:
                id_card_data["details"]["id_number"] = id_number_match.group(0)
                break

    return id_card_data

def get_best_name_variation(name_variations: list) -> str:
    counter = Counter(name_variations)
    most_common_name, _ = counter.most_common(1)[0]
    return most_common_name

def beautify_extracted_text(text: str, blur_text: str, doc_type: str) -> Dict:
    if doc_type == "id_card":
        return beautify_id_card(text, blur_text)
    else:
        return {"raw_text": text}
