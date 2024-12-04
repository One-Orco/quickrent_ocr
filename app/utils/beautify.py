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
def beautify_license_deed(text: str) -> Dict[str, Union[str, Dict[str, str]]]:
    deed_data = {
        "issue_date": "",
        "mortgage_status": "",
        "property_type": "",
        "community": "",
        "plot_no": "",
        "municipality_no": "",
        "building_no": "",
        "building_name": "",
        "property_no": "",
        "floor_no": "",
        "parkings": "",
        "suite_area": "",
        "balcony_area": "",
        "area_sq_meter": "",
        "area_sq_feet": "",
        "common_area": "",
        "owners_and_shares": ""
    }

    # Preprocessing: Clean up text by replacing unwanted characters and normalizing
    clean_text = re.sub(r'[^a-zA-Z0-9/\n\s:-]', '', text)  # Remove unwanted characters
    clean_text = re.sub(r' +', ' ', clean_text)  # Replace multiple spaces with a single space

    lines = clean_text.splitlines()

    # Using heuristic to find details
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Issue Date detection
        if "issue date" in line_lower:
            date_match = re.search(r'\d{2}-\d{2}-\d{4}', line)
            if date_match:
                deed_data["issue_date"] = date_match.group(0)

        # Mortgage Status detection
        if "mortgage status" in line_lower:
            deed_data["mortgage_status"] = line.split(':')[-1].strip()

        # Property Type detection
        if "property type" in line_lower:
            deed_data["property_type"] = line.split(':')[-1].strip()

        # Community detection
        if "community" in line_lower:
            deed_data["community"] = line.split(':')[-1].strip()

        # Plot No detection
        if "plot no" in line_lower:
            deed_data["plot_no"] = line.split(':')[-1].strip()

        # Municipality No detection
        if "municipality no" in line_lower:
            deed_data["municipality_no"] = line.split(':')[-1].strip()

        # Building No detection
        if "building no" in line_lower:
            deed_data["building_no"] = line.split(':')[-1].strip()

        # Building Name detection
        if "building name" in line_lower:
            deed_data["building_name"] = line.split(':')[-1].strip()

        # Property No detection
        if "property no" in line_lower:
            deed_data["property_no"] = line.split(':')[-1].strip()

        # Floor No detection
        if "floor no" in line_lower:
            deed_data["floor_no"] = line.split(':')[-1].strip()

        # Parkings detection
        if "parkings" in line_lower:
            deed_data["parkings"] = line.split(':')[-1].strip()

        # Suite Area detection
        if "suite area" in line_lower:
            deed_data["suite_area"] = line.split(':')[-1].strip()

        # Balcony Area detection
        if "balcony area" in line_lower:
            deed_data["balcony_area"] = line.split(':')[-1].strip()

        # Area Sq Meter detection
        if "area sq meter" in line_lower:
            deed_data["area_sq_meter"] = line.split(':')[-1].strip()

        # Area Sq Feet detection
        if "area sq feet" in line_lower:
            deed_data["area_sq_feet"] = line.split(':')[-1].strip()

        # Common Area detection
        if "common area" in line_lower:
            deed_data["common_area"] = line.split(':')[-1].strip()

        # Owners and their shares detection
        if "owners and their shares" in line_lower:
            if i + 1 < len(lines):
                deed_data["owners_and_shares"] = lines[i + 1].strip()

    return deed_data
# Function to select appropriate beautifier based on document type
def beautify_extracted_text(text: str, blur_text: str, doc_type: str) -> Dict:
    if doc_type == "id_card":
        return beautify_id_card(text, blur_text)
    elif doc_type == "license_deed":
        return beautify_license_deed(text)
    else:
        return {"raw_text": text}