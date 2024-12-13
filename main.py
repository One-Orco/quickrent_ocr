import json
import boto3
from fastapi import FastAPI, File, UploadFile, HTTPException,Query
from fastapi.responses import JSONResponse
from enum import Enum
from pydantic import BaseModel
from typing import Optional



app = FastAPI()
class DocumentType(str, Enum):
    id_card = "id_card"
    passport = "passport"
    title_deed = "title_deed"
    commercial_license = "commercial_license"

class DocumentRequest(BaseModel):
    doc_type: DocumentType
textract = boto3.client('textract')

class DocumentProcessor:
    def __init__(self, query_mapping):
        self.query_mapping = query_mapping

    def format_date(self, date):
        if len(date) == 6 and date.isdigit():
            year = int(date[:2])
            century = "19" if year > 50 else "20"
            return f"{date[4:6]}/{date[2:4]}/{century}{year}"
        return "Invalid"

    def parse_mrz(self, mrz):
        lines = mrz.splitlines()
        if len(lines) < 3:
            return None
        line1 = lines[0]
        line2 = lines[1]
        line3 = lines[2]
        parsed = {
            "id_card_number": line1[5:30].replace("<", ""),
            "date_of_birth": line2[:6],
            "gender": line2[7],
            "expiration_date": line2[8:14],
            "full_name": line3.replace("<", " ").strip()
        }
        parsed["date_of_birth"] = self.format_date(parsed["date_of_birth"])
        parsed["expiration_date"] = self.format_date(parsed["expiration_date"])
        return parsed

    def process_front(self, front_file_bytes):
        front_response = textract.analyze_document(
            Document={'Bytes': front_file_bytes},
            FeatureTypes=["QUERIES"],
            QueriesConfig={"Queries": [{"Text": question} for question in self.query_mapping.values()]}
        )

        front_results = [block for block in front_response.get("Blocks", []) if block["BlockType"] == "QUERY_RESULT"]
        results = {
            key: (front_results[i].get("Text", "Not Available") if i < len(front_results) else "Not Available")
            for i, key in enumerate(self.query_mapping.keys())
        }
        return results

class IDCardProcessor(DocumentProcessor):
    def process_back(self, back_file_bytes, results):
        back_response = textract.detect_document_text(
            Document={'Bytes': back_file_bytes}
        )
        mrz_lines = []
        for block in back_response.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "")
                if text.startswith("IL") or "<<" in text:
                    mrz_lines.append(text)

        mrz_text = "\n".join(mrz_lines) if mrz_lines else "Not Available"
        results["mrz"] = mrz_text

        if mrz_text != "Not Available" and len(mrz_lines) >= 3:
            mrz_data = self.parse_mrz(mrz_text)
            if mrz_data:
                results.update({
                    "mrz_id_card_number": mrz_data["id_card_number"],
                    "mrz_date_of_birth": mrz_data["date_of_birth"],
                    "mrz_expiration_date": mrz_data["expiration_date"],
                    "mrz_gender": mrz_data["gender"],
                    "mrz_full_name": mrz_data["full_name"],
                    "date_of_birth_validation": (
                        "Valid" if results["date_of_birth"] == mrz_data["date_of_birth"] else "Mismatch"
                    ),
                    "expiration_date_validation": (
                        "Valid" if results["expiration_date"] == mrz_data["expiration_date"] else "Mismatch"
                    )
                })
            else:
                results["mrz_validation"] = "Invalid"

        return results

class PassportProcessor(DocumentProcessor):
    def parse_mrz(self, mrz):

        lines = mrz.splitlines()
        if len(lines) < 2:
            return None  

        line1 = lines[0] 
        line2 = lines[1]  

        parsed = {
            "passport_number": line2[:9].replace("<", ""),  
            "nationality": line2[10:13],  
            "date_of_birth": self.format_date(line2[13:19]),  
            "gender": line2[20],
            "expiration_date": self.format_date(line2[21:27]),  
            "full_name": line1[5:].replace("<", " ").strip()  
        }
        return parsed

    def process_front(self, front_file_bytes):

        front_response = textract.analyze_document(
            Document={'Bytes': front_file_bytes},
            FeatureTypes=["QUERIES"],
            QueriesConfig={"Queries": [{"Text": question, "Alias": alias} for alias, question in self.query_mapping.items()]}
        )

        
        query_id_to_text = {
            block["Id"]: block.get("Text", "Not Available")
            for block in front_response.get("Blocks", [])
            if block["BlockType"] == "QUERY_RESULT"
        }

        
        results = {}
        for block in front_response.get("Blocks", []):
            if block["BlockType"] == "QUERY" and "Relationships" in block:
                query_id = block["Id"]
                alias = block["Query"].get("Alias", block["Query"]["Text"])
                for relationship in block["Relationships"]:
                    if relationship["Type"] == "ANSWER":
                        for answer_id in relationship["Ids"]:
                            results[alias] = query_id_to_text.get(answer_id, "Not Available")

        mrz_lines = []
        for block in front_response.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "")
                if text.startswith("P<") or "<<" in text:  
                    mrz_lines.append(text)

        mrz_text = "\n".join(mrz_lines) if mrz_lines else "Not Available"
        results["mrz"] = mrz_text

        if mrz_text != "Not Available" and len(mrz_lines) >= 2:
            mrz_data = self.parse_mrz(mrz_text)
            if mrz_data:
                results["full_name"] = mrz_data["full_name"]
                results.update({
                    "mrz_passport_number": mrz_data["passport_number"],
                    "mrz_date_of_birth": mrz_data["date_of_birth"],
                    "mrz_expiration_date": mrz_data["expiration_date"],
                    "mrz_gender": mrz_data["gender"],
                    "mrz_full_name": mrz_data["full_name"]
                })
                results["date_of_birth_validation"] = (
                    "Valid" if results.get("date_of_birth") == mrz_data["date_of_birth"] else "Mismatch"
                )
                results["expiration_date_validation"] = (
                    "Valid" if results.get("date_of_expiry") == mrz_data["expiration_date"] else "Mismatch"
                )
                if results["date_of_birth_validation"] == "Mismatch":
                    results["ocr_date_of_birth"] = results.get("date_of_birth", "Not Available")
                    results["mrz_date_of_birth_value"] = mrz_data["date_of_birth"]
                if results["expiration_date_validation"] == "Mismatch":
                    results["ocr_date_of_expiry"] = results.get("date_of_expiry", "Not Available")
                    results["mrz_expiration_date_value"] = mrz_data["expiration_date"]
            else:
                results["mrz_validation"] = "Invalid"

        return results


class TitleDeedProcessor(DocumentProcessor):
    def process_front(self, front_file_bytes):
        front_response = textract.analyze_document(
            Document={'Bytes': front_file_bytes},
            FeatureTypes=["QUERIES"],
            QueriesConfig={
                "Queries": [{"Text": question, "Alias": alias} for alias, question in self.query_mapping.items()]
            }
        )

        # with open('title_deed_response.json', 'w') as f:
        #     json.dump(front_response, f, indent=4)

        query_id_to_text = {
            block["Id"]: block.get("Text", "Not Available")
            for block in front_response.get("Blocks", [])
            if block["BlockType"] == "QUERY_RESULT"
        }

        results = {}
        for block in front_response.get("Blocks", []):
            if block["BlockType"] == "QUERY" and "Relationships" in block:
                query_id = block["Id"]
                alias = block["Query"].get("Alias", block["Query"]["Text"])
                for relationship in block["Relationships"]:
                    if relationship["Type"] == "ANSWER":
                        for answer_id in relationship["Ids"]:
                            results[alias] = query_id_to_text.get(answer_id, "Not Available")

        return results



class CommercialLicenseProcessor(DocumentProcessor):
    def process_front(self, front_file_bytes):
        front_response = textract.analyze_document(
            Document={'Bytes': front_file_bytes},
            FeatureTypes=["QUERIES"],
            QueriesConfig={"Queries": [{"Text": question, "Alias": alias} for alias, question in self.query_mapping.items()]}
        )

        query_id_to_text = {
            block["Id"]: block.get("Text", "Not Available")
            for block in front_response.get("Blocks", [])
            if block["BlockType"] == "QUERY_RESULT"
        }

        results = {}
        for block in front_response.get("Blocks", []):
            if block["BlockType"] == "QUERY" and "Relationships" in block:
                query_id = block["Id"]
                alias = block["Query"].get("Alias", block["Query"]["Text"])
                for relationship in block["Relationships"]:
                    if relationship["Type"] == "ANSWER":
                        for answer_id in relationship["Ids"]:
                            results[alias] = query_id_to_text.get(answer_id, "Not Available")

        return results


PROCESSORS = {
    "id_card": IDCardProcessor,
    "passport": PassportProcessor,
    "title_deed": TitleDeedProcessor,
    "commercial_license": CommercialLicenseProcessor
}

QUERY_MAPPING = {
    "id_card": {
        "id_card_number": "What is the ID card number?",
        "full_name": "What is the full name?",
        "date_of_birth": "What is the date of birth?",
        "expiration_date": "What is the expiration date?",
        "issuing_authority": "What is the issuing authority?",
        "nationality": "What is the nationality?",
        "sex": "What is the sex?"
    },
    "passport": {
        "passport_number": "What is the passport number?",
        "nationality": "What is the nationality?",
        "date_of_birth": "What is the date of birth?",
        "date_of_expiry": "what is date of expire?",
        "sex": "what is sex"
    },
    "title_deed": {
        "deed_number": "What is the deed number?",
        "owner_name": "Who is the owner of the property?",
        "property_mortage": "What is mortgage status?",
        "property_type": "What is the property type?",
        "community": "what is community?",
        "property_no": "What is the property no?",
        "issue_date": "What is the issue date?",
        "building_name": "what is building name?",
        "building_no": "what is building no?",
        "floor" : "what is the floor?",
        "plot_no": "what is plot no?",
        "parkings": "what is parkings?",
        "area_square_meter": "what is area meter?",
        "balcony_area": "what is balcony area?"

    },
    "commercial_license": {
        "license_number": "What is the license number?",
        "business_name": "What is the name of the business?",
        "business_type": "What is the business type?",
        "expiration_date": "What is the expiration date?",
        "issuing_authority": "Who is the issuing authority?"
    }
}

@app.post("/process-document/")
async def process_document(
    doc_type: DocumentType = Query(..., description="Select the type of document to process"),
    front_file: UploadFile = File(...),
    back_file: Optional[UploadFile] = File(None, description="Optional back file for documents like ID cards")
):
    # Ensure back_file is not empty when required
    if doc_type == DocumentType.id_card and back_file is None:
        raise HTTPException(status_code=400, detail="back_file is required for ID cards")

    processor_class = PROCESSORS[doc_type]
    processor = processor_class(QUERY_MAPPING[doc_type])

    try:
        front_file_bytes = await front_file.read()
        back_file_bytes = await back_file.read() if back_file else None

        results = processor.process_front(front_file_bytes)

        if doc_type == "id_card" and back_file_bytes:
            results = processor.process_back(back_file_bytes, results)

        return JSONResponse(content=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))