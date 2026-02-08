"""
Sample code demonstrating authentication with YatinVeda API
"""

import requests
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

def register_user(email: str, password: str, role: str = "user") -> dict:
    """
    Register a new user
    
    Args:
        email: User's email address
        password: User's password
        role: User role (user or practitioner)
    
    Returns:
        Response data including user ID and tokens
    """
    url = f"{BASE_URL}/auth/register"
    payload = {
        "email": email,
        "password": password,
        "role": role
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def login_user(email: str, password: str) -> dict:
    """
    Login and get access tokens
    
    Args:
        email: User's email
        password: User's password
    
    Returns:
        Response data including access and refresh tokens
    """
    url = f"{BASE_URL}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_user_profile(access_token: str) -> dict:
    """
    Get current user profile
    
    Args:
        access_token: JWT access token
    
    Returns:
        User profile data
    """
    url = f"{BASE_URL}/users/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def refresh_token(refresh_token: str) -> dict:
    """
    Refresh access token
    
    Args:
        refresh_token: JWT refresh token
    
    Returns:
        New access token
    """
    url = f"{BASE_URL}/auth/refresh"
    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }
    
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    # Register a new user
    print("Registering new user...")
    registration = register_user(
        email="user@example.com",
        password="SecurePassword123!",
        role="user"
    )
    print(f"Registered user ID: {registration.get('user_id')}")
    
    # Login
    print("\nLogging in...")
    login_response = login_user(
        email="user@example.com",
        password="SecurePassword123!"
    )
    access_token = login_response.get("access_token")
    refresh_token_str = login_response.get("refresh_token")
    print("Login successful!")
    
    # Get profile
    print("\nFetching user profile...")
    profile = get_user_profile(access_token)
    print(f"User email: {profile.get('email')}")
    print(f"User role: {profile.get('role')}")
    
    # Refresh token
    print("\nRefreshing access token...")
    new_token = refresh_token(refresh_token_str)
    print("Token refreshed successfully!")
