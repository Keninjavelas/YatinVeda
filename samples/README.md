# YatinVeda API Sample Code

This directory contains sample code demonstrating how to interact with the YatinVeda API.

## Prerequisites

Install the required dependencies:

```bash
pip install requests
```

## Available Samples

### 1. Authentication (`sample_authentication.py`)

Demonstrates basic authentication flows:
- User registration
- Login and token management
- Getting user profile
- Token refresh

**Run:**
```bash
python sample_authentication.py
```

### 2. Multi-Factor Authentication (`sample_mfa_flow.py`)

Shows how to implement MFA in your application:
- Enabling MFA for a user
- Verifying MFA setup with TOTP
- Logging in with MFA
- Disabling MFA

**Run:**
```bash
python sample_mfa_flow.py
```

### 3. Booking System (`sample_booking.py`)

Demonstrates appointment booking functionality:
- Finding practitioners by specialty
- Checking practitioner availability
- Creating bookings
- Viewing and managing bookings
- Cancelling appointments

**Run:**
```bash
python sample_booking.py
```

### 4. Prescription Management (`sample_prescription.py`)

Shows prescription creation and management:
- Creating prescriptions (practitioner)
- Viewing prescriptions (patient)
- Downloading prescription PDFs
- Updating prescription status

**Run:**
```bash
python sample_prescription.py
```

## Configuration

Before running the samples, make sure to:

1. Update the `BASE_URL` in each file to match your API endpoint
2. Replace placeholder tokens with actual access tokens from your authentication flow
3. Ensure the backend API is running

## API Documentation

For full API documentation, see [docs/api/API_DOCUMENTATION.md](../docs/api/API_DOCUMENTATION.md)

## Support

For issues or questions, please refer to the main project documentation or open an issue on GitHub.
