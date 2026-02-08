"""
Sample code demonstrating Multi-Factor Authentication (MFA) flow
"""

import requests
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

def enable_mfa(access_token: str) -> dict:
    """
    Enable MFA for the current user
    
    Args:
        access_token: JWT access token
    
    Returns:
        QR code data and secret key for authenticator app
    """
    url = f"{BASE_URL}/auth/mfa/enable"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()


def verify_mfa_setup(access_token: str, totp_code: str) -> dict:
    """
    Verify MFA setup with TOTP code from authenticator app
    
    Args:
        access_token: JWT access token
        totp_code: 6-digit code from authenticator app
    
    Returns:
        Verification status and backup codes
    """
    url = f"{BASE_URL}/auth/mfa/verify"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "totp_code": totp_code
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def login_with_mfa(email: str, password: str, totp_code: str) -> dict:
    """
    Login with MFA enabled
    
    Args:
        email: User's email
        password: User's password
        totp_code: 6-digit TOTP code
    
    Returns:
        Access and refresh tokens
    """
    url = f"{BASE_URL}/auth/login-mfa"
    payload = {
        "email": email,
        "password": password,
        "totp_code": totp_code
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def disable_mfa(access_token: str, totp_code: str) -> dict:
    """
    Disable MFA for the current user
    
    Args:
        access_token: JWT access token
        totp_code: Current TOTP code for verification
    
    Returns:
        Confirmation of MFA disabled
    """
    url = f"{BASE_URL}/auth/mfa/disable"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "totp_code": totp_code
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


# Example usage
if __name__ == "__main__":
    # Assume user is already logged in
    access_token = "your_access_token_here"
    
    # Step 1: Enable MFA
    print("Enabling MFA...")
    mfa_setup = enable_mfa(access_token)
    secret = mfa_setup.get("secret")
    qr_code_url = mfa_setup.get("qr_code")
    print(f"Scan this QR code with your authenticator app: {qr_code_url}")
    print(f"Or enter this secret manually: {secret}")
    
    # Step 2: Verify setup with TOTP code
    totp_code = input("Enter the 6-digit code from your authenticator app: ")
    print("\nVerifying MFA setup...")
    verification = verify_mfa_setup(access_token, totp_code)
    backup_codes = verification.get("backup_codes", [])
    print("MFA enabled successfully!")
    print(f"Save these backup codes: {backup_codes}")
    
    # Step 3: Login with MFA
    print("\nTesting MFA login...")
    totp_code_login = input("Enter the current 6-digit code for login: ")
    login_response = login_with_mfa(
        email="user@example.com",
        password="SecurePassword123!",
        totp_code=totp_code_login
    )
    print("Login with MFA successful!")
    print(f"Access token: {login_response.get('access_token')[:20]}...")
