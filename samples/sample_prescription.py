"""
Sample code demonstrating prescription management
"""

import requests
from typing import List, Optional

BASE_URL = "http://localhost:8000/api/v1"

def create_prescription(access_token: str, patient_id: int, 
                       diagnosis: str, medicines: List[dict], 
                       notes: Optional[str] = None) -> dict:
    """
    Create a new prescription (practitioner only)
    
    Args:
        access_token: JWT access token (practitioner)
        patient_id: Patient's user ID
        diagnosis: Medical diagnosis
        medicines: List of medicine objects with name, dosage, duration
        notes: Additional notes (optional)
    
    Returns:
        Created prescription with ID
    """
    url = f"{BASE_URL}/prescriptions"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "patient_id": patient_id,
        "diagnosis": diagnosis,
        "medicines": medicines,
        "notes": notes
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def get_patient_prescriptions(access_token: str) -> List[dict]:
    """
    Get prescriptions for current patient
    
    Args:
        access_token: JWT access token (patient)
    
    Returns:
        List of prescriptions
    """
    url = f"{BASE_URL}/prescriptions/my-prescriptions"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_prescription_pdf(access_token: str, prescription_id: int) -> bytes:
    """
    Download prescription as PDF
    
    Args:
        access_token: JWT access token
        prescription_id: Prescription ID
    
    Returns:
        PDF file content as bytes
    """
    url = f"{BASE_URL}/prescriptions/{prescription_id}/pdf"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content


def update_prescription_status(access_token: str, prescription_id: int, 
                               status: str) -> dict:
    """
    Update prescription status
    
    Args:
        access_token: JWT access token (practitioner)
        prescription_id: Prescription ID
        status: New status (active, completed, cancelled)
    
    Returns:
        Updated prescription
    """
    url = f"{BASE_URL}/prescriptions/{prescription_id}/status"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "status": status
    }
    
    response = requests.patch(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    practitioner_token = "practitioner_access_token_here"
    patient_token = "patient_access_token_here"
    
    # Practitioner creates prescription
    print("Creating prescription...")
    medicines = [
        {
            "name": "Ashwagandha Churna",
            "dosage": "1 teaspoon twice daily",
            "duration": "30 days",
            "instructions": "Take with warm milk before meals"
        },
        {
            "name": "Triphala",
            "dosage": "2 tablets at night",
            "duration": "30 days",
            "instructions": "Take with warm water before bed"
        }
    ]
    
    prescription = create_prescription(
        practitioner_token,
        patient_id=123,
        diagnosis="Vata imbalance, stress-related symptoms",
        medicines=medicines,
        notes="Avoid cold foods and drinks. Follow dosha-balancing diet."
    )
    prescription_id = prescription["id"]
    print(f"Prescription created with ID: {prescription_id}")
    
    # Patient views their prescriptions
    print("\nPatient viewing prescriptions...")
    my_prescriptions = get_patient_prescriptions(patient_token)
    for rx in my_prescriptions:
        print(f"\nPrescription #{rx['id']}")
        print(f"Date: {rx['created_at']}")
        print(f"Diagnosis: {rx['diagnosis']}")
        print(f"Medicines: {len(rx['medicines'])} items")
    
    # Download prescription PDF
    print(f"\nDownloading prescription #{prescription_id} as PDF...")
    pdf_content = get_prescription_pdf(patient_token, prescription_id)
    with open(f"prescription_{prescription_id}.pdf", "wb") as f:
        f.write(pdf_content)
    print(f"PDF saved as prescription_{prescription_id}.pdf")
    
    # Practitioner marks prescription as completed
    print(f"\nUpdating prescription status to completed...")
    updated = update_prescription_status(
        practitioner_token,
        prescription_id,
        "completed"
    )
    print(f"Prescription status: {updated['status']}")
