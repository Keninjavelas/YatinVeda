"""
Sample code demonstrating booking appointments with practitioners
"""

import requests
from datetime import datetime, timedelta
from typing import List, Optional

BASE_URL = "http://localhost:8000/api/v1"

def get_practitioners(access_token: str, specialty: Optional[str] = None) -> List[dict]:
    """
    Get list of available practitioners
    
    Args:
        access_token: JWT access token
        specialty: Filter by specialty (optional)
    
    Returns:
        List of practitioner profiles
    """
    url = f"{BASE_URL}/practitioners"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {}
    if specialty:
        params["specialty"] = specialty
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_practitioner_availability(access_token: str, practitioner_id: int, date: str) -> dict:
    """
    Get practitioner's available time slots
    
    Args:
        access_token: JWT access token
        practitioner_id: Practitioner's user ID
        date: Date in YYYY-MM-DD format
    
    Returns:
        Available time slots
    """
    url = f"{BASE_URL}/practitioners/{practitioner_id}/availability"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "date": date
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def create_booking(access_token: str, practitioner_id: int, 
                   appointment_time: str, service_type: str) -> dict:
    """
    Book an appointment with a practitioner
    
    Args:
        access_token: JWT access token
        practitioner_id: Practitioner's user ID
        appointment_time: Appointment time in ISO format
        service_type: Type of service (consultation, therapy, etc.)
    
    Returns:
        Booking confirmation details
    """
    url = f"{BASE_URL}/bookings"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "practitioner_id": practitioner_id,
        "appointment_time": appointment_time,
        "service_type": service_type
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def get_my_bookings(access_token: str, status: Optional[str] = None) -> List[dict]:
    """
    Get user's bookings
    
    Args:
        access_token: JWT access token
        status: Filter by status (pending, confirmed, completed, cancelled)
    
    Returns:
        List of bookings
    """
    url = f"{BASE_URL}/bookings/my-bookings"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {}
    if status:
        params["status"] = status
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def cancel_booking(access_token: str, booking_id: int, reason: str) -> dict:
    """
    Cancel a booking
    
    Args:
        access_token: JWT access token
        booking_id: Booking ID
        reason: Reason for cancellation
    
    Returns:
        Cancellation confirmation
    """
    url = f"{BASE_URL}/bookings/{booking_id}/cancel"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "reason": reason
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    access_token = "your_access_token_here"
    
    # Find practitioners
    print("Finding Ayurvedic practitioners...")
    practitioners = get_practitioners(access_token, specialty="ayurveda")
    print(f"Found {len(practitioners)} practitioners")
    
    if practitioners:
        practitioner = practitioners[0]
        practitioner_id = practitioner["id"]
        print(f"\nSelected: {practitioner['name']}")
        
        # Check availability for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\nChecking availability for {tomorrow}...")
        availability = get_practitioner_availability(
            access_token, 
            practitioner_id, 
            tomorrow
        )
        
        if availability.get("available_slots"):
            # Book first available slot
            first_slot = availability["available_slots"][0]
            print(f"\nBooking appointment at {first_slot}...")
            booking = create_booking(
                access_token,
                practitioner_id,
                first_slot,
                "consultation"
            )
            print(f"Booking confirmed! Booking ID: {booking['id']}")
            
            # View all bookings
            print("\nMy upcoming bookings:")
            bookings = get_my_bookings(access_token, status="confirmed")
            for b in bookings:
                print(f"- {b['appointment_time']} with {b['practitioner_name']}")
