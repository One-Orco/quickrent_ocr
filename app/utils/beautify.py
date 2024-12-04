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


# Function to select appropriate beautifier based on document type
def beautify_extracted_text(text: str, blur_text: str, doc_type: str) -> Dict:
    if doc_type == "id_card":
        return beautify_id_card(text, blur_text)
    elif doc_type == "title_deed":
        print(text)
        
        return beautify_title_deed(text)
    else:
        return {"raw_text": text}
    
    # Correct common OCR errors in dates (e.g., interpreting incorrect symbols)
def correct_date(date_str: str) -> str:
    corrected_date = re.sub(r'[^0-9/]', '', date_str)  # Remove any unexpected characters
    parts = corrected_date.split('/')
    if len(parts) == 3:
        day, month, year = parts
        day = day if day.isdigit() and 1 <= int(day) <= 31 else "01"
        month = month if month.isdigit() and 1 <= int(month) <= 12 else "01"
        year = year if len(year) == 4 else "2000"
        return f"{day}/{month}/{year}"
    return corrected_date

# Determine the best name variation based on frequency and length
def get_best_name_variation(name_variations: list) -> str:
    # Use a Counter to find the most common names
    counter = Counter(name_variations)
    most_common_name, _ = counter.most_common(1)[0]
    return most_common_name



def beautify_title_deed(text: str) -> Dict[str, Union[str, Dict[str, str]]]:
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

    # Clean and normalize the text
    clean_text = re.sub(r'[^a-zA-Z0-9\n\s.,:/-]', '', text)  # Allow slashes and hyphens for dates
    clean_text = re.sub(r' +', ' ', clean_text)  # Normalize spaces
    clean_text = re.sub(r':\s*$', '', clean_text, flags=re.MULTILINE)  # Remove trailing colons
    lines = clean_text.splitlines()

    # Extract issue_date specifically
    for line in lines:
        if "issue date" in line.lower() or "تاريخ الإصدار" in line.lower():
            # Match multiple date formats
            date_match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', line)
            if date_match:
                deed_data["issue_date"] = date_match.group(0)
                break

    # Define mappings for other fields
    field_mappings = {
        "mortgage_status": ["mortgage status", "حالة الرهن"],
        "property_type": ["property type", "نوع العقار"],
        "community": ["community", "المنطقة"],
        "plot_no": ["plot no", "رقم الأرض"],
        "municipality_no": ["municipality no", "رقم البلدية"],
        "building_no": ["building no", "رقم المبنى"],
        "building_name": ["building name", "اسم المبنى"],
        "property_no": ["property no", "رقم العقار"],
        "floor_no": ["floor no", "رقم الطابق"],
        "parkings": ["parkings", "المواقف"],
        "suite_area": ["suite area", "المساحة الداخلية"],
        "balcony_area": ["balcony area", "مساحة البلكونة"],
        "area_sq_meter": ["area sq meter", "المساحة الكلية مثر مربع"],
        "area_sq_feet": ["area sq feet", "المساحة الكلية بالقدم المربع"],
        "common_area": ["common area", "المساحة المشتركة"],
        "owners_and_shares": ["owners and their shares", "أسماء الملاك وحخصصهم"]
    }

    # Extract fields using the mappings
    for line in lines:
        line_lower = line.lower().strip()
        for field, keywords in field_mappings.items():
            if any(keyword.lower() in line_lower for keyword in keywords):
                value_match = re.search(r':\s*(.+)', line)
                if value_match:
                    value = value_match.group(1).strip()
                    deed_data[field] = value
                break

    # Additional cleaning for specific fields
    def clean_field(value: str, remove: list = None) -> str:
        if not value:
            return ""
        if remove:
            for word in remove:
                value = value.replace(word, "")
        return value.strip()

    # Apply specific cleanups for fields
    deed_data["mortgage_status"] = clean_field(deed_data["mortgage_status"], [":", "Mortgage Status"])
    deed_data["property_type"] = clean_field(deed_data["property_type"], [":", "Property Type"])
    deed_data["community"] = clean_field(deed_data["community"], [":"])
    deed_data["plot_no"] = clean_field(deed_data["plot_no"], [":"])
    deed_data["municipality_no"] = clean_field(deed_data["municipality_no"], [":", "-"])
    deed_data["building_no"] = clean_field(deed_data["building_no"], [":"])
    deed_data["building_name"] = clean_field(deed_data["building_name"], [":", "-"])
    deed_data["property_no"] = clean_field(deed_data["property_no"], [":"])
    deed_data["floor_no"] = clean_field(deed_data["floor_no"], [":"])
    deed_data["parkings"] = clean_field(deed_data["parkings"], [":"])
    deed_data["common_area"] = clean_field(deed_data["common_area"], [":", "wall"])
    deed_data["owners_and_shares"] = clean_field(deed_data["owners_and_shares"], [":", "wall"])

    # Ensure numeric fields are clean
    def extract_number(value: str) -> str:
        match = re.search(r'\d+\.\d+', value)
        return match.group(0) if match else ""

    deed_data["suite_area"] = extract_number(deed_data["suite_area"])
    deed_data["balcony_area"] = extract_number(deed_data["balcony_area"])
    deed_data["area_sq_meter"] = extract_number(deed_data["area_sq_meter"])
    deed_data["area_sq_feet"] = extract_number(deed_data["area_sq_feet"])

    return deed_data








def remove_unlikely_english_words(text: str) -> str:
    def is_likely_english(word: str) -> bool:
        # Check if the word has typical English patterns
        return re.match(r'^[a-zA-Z]+$', word) and not re.match(r'[b-df-hj-np-tv-z]{4,}', word)

    lines = text.splitlines()
    filtered_lines = []

    for line in lines:
        words = line.split()
        english_words = [word for word in words if is_likely_english(word)]
        if english_words:
            filtered_lines.append(" ".join(english_words))

    return "\n".join(filtered_lines)
