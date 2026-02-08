# YatinVeda API Documentation

## Overview

YatinVeda is a hybrid AI-assisted Vedic Astrology Intelligence Platform with features including birth chart management, guru consultation booking, AI-powered VedaMind chat, prescription PDF generation, and community features.

## Base URL
`http://localhost:8000` (development) or your production URL

## Authentication

Most endpoints require authentication using JWT tokens obtained through the `/auth/login` endpoint.

### Getting an Access Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username_or_email",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "..."
}
```

### Using the Access Token

Include the access token in the Authorization header for protected endpoints:

```bash
curl -X GET "http://localhost:8000/api/v1/profile" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## API Endpoints

### Authentication (`/api/v1/auth`)

#### Register User
- **POST** `/api/v1/auth/register/legacy`
- **Description**: Register a new user account
- **Request Body**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Full Name"
}
```
- **Response**:
```json
{
  "message": "User registered successfully",
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": 1
}
```

#### Login User
- **POST** `/api/v1/auth/login`
- **Description**: Authenticate user and get access token
- **Request Body**:
```json
{
  "username": "string",
  "password": "string",
  "mfa_code": "optional_6_digit_code"
}
```
- **Response**:
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 1800,
  "requires_mfa": false,
  "mfa_token": null
}
```

#### Get User Profile
- **GET** `/api/v1/profile`
- **Description**: Get current user's profile information
- **Authentication Required**: Yes
- **Response**:
```json
{
  "username": "string",
  "email": "user@example.com",
  "full_name": "Full Name",
  "created_at": "2023-01-01T00:00:00",
  "is_admin": false,
  "role": "user",
  "verification_status": "active",
  "practitioner_profile": null
}
```

#### Update User Profile
- **PUT** `/api/v1/profile`
- **Description**: Update current user's profile information
- **Authentication Required**: Yes
- **Request Body**:
```json
{
  "full_name": "New Full Name",
  "email": "newemail@example.com"
}
```
- **Response**:
```json
{
  "message": "Profile updated successfully",
  "username": "string",
  "email": "newemail@example.com",
  "full_name": "New Full Name"
}
```

### Community (`/api/v1/community`)

#### Create Post
- **POST** `/api/v1/community/posts`
- **Description**: Create a new community post
- **Authentication Required**: Yes
- **Request Body**:
```json
{
  "title": "Post Title",
  "content": "Post content here...",
  "tags": ["tag1", "tag2"],
  "visibility": "public"
}
```
- **Response**:
```json
{
  "id": 1,
  "title": "Post Title",
  "content": "Post content here...",
  "author": {
    "id": 1,
    "username": "username"
  },
  "tags": ["tag1", "tag2"],
  "visibility": "public",
  "created_at": "2023-01-01T00:00:00"
}
```

#### Like a Post
- **POST** `/api/v1/community/posts/{post_id}/like`
- **Description**: Like a community post
- **Authentication Required**: Yes
- **Parameters**:
  - `post_id`: ID of the post to like
- **Response**: 201 Created

#### Add Comment to Post
- **POST** `/api/v1/community/posts/{post_id}/comments`
- **Description**: Add a comment to a post
- **Authentication Required**: Yes
- **Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
```json
{
  "content": "Comment content"
}
```
- **Response**:
```json
{
  "id": 1,
  "content": "Comment content",
  "author": {
    "id": 1,
    "username": "username"
  },
  "created_at": "2023-01-01T00:00:00"
}
```

### Chat (`/api/v1/chat`)

#### Send Chat Message
- **POST** `/api/v1/chat/message`
- **Description**: Send a message to the AI chat system
- **Authentication Required**: Yes
- **Request Body**:
```json
{
  "message": "Your question or message",
  "provider": "ollama",
  "model": "llama3.1:8b-instruct-q4_K_M"
}
```
- **Response**:
```json
{
  "response": "AI response to your message",
  "model_used": "llama3.1:8b-instruct-q4_K_M",
  "tokens_used": 120
}
```

### Guru Booking (`/api/v1/guru-booking`)

#### Book Guru Consultation
- **POST** `/api/v1/guru-booking/book`
- **Description**: Book a consultation with a guru
- **Authentication Required**: Yes
- **Request Body**:
```json
{
  "guru_id": 1,
  "date": "2023-01-01",
  "time_slot": "10:00-11:00",
  "duration_hours": 1,
  "special_request": "Special request for the consultation"
}
```
- **Response**:
```json
{
  "booking_id": 1,
  "status": "confirmed",
  "guru": {
    "id": 1,
    "name": "Guru Name"
  },
  "booking_date": "2023-01-01",
  "time_slot": "10:00-11:00"
}
```

### Payments (`/api/v1/payments`)

#### Create Order
- **POST** `/api/v1/payments/create-order`
- **Description**: Create a payment order for Razorpay
- **Authentication Required**: Yes
- **Request Body**:
```json
{
  "amount": 5000,
  "currency": "INR",
  "purpose": "Guru Consultation"
}
```
- **Response**:
```json
{
  "order_id": "order_123456789",
  "amount": 5000,
  "currency": "INR",
  "razorpay_key": "rzp_test_123456789"
}
```

### Health Check (`/api/v1/health`)

#### Health Check
- **GET** `/api/v1/health`
- **Description**: Check API health status
- **Authentication Required**: No
- **Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## CSRF Protection

For state-changing operations, the application implements CSRF protection:

1. **Double-submit cookie pattern**: CSRF token is set in a cookie and must be submitted with requests
2. **Header validation**: Include `X-CSRF-Token` header with the token value
3. **Form field**: Include `csrf_token` field in form submissions

To get a CSRF token:
```bash
curl -X GET "http://localhost:8000/api/v1/security/csrf-token" \
  -H "Authorization: Bearer your_token"
```

Then use the token in subsequent requests:
```bash
curl -X POST "http://localhost:8000/api/v1/profile" \
  -H "Authorization: Bearer your_token" \
  -H "X-CSRF-Token: csrf_token_value" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "New Name"}'
```

## Rate Limiting

The API implements rate limiting:
- Anonymous requests: 100 per minute
- Authenticated requests: 1000 per minute
- Login attempts: 5 per hour with progressive delays
- Registration attempts: 3 per 5 minutes

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp for when the current window resets

## Error Handling

Standard error response format:
```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `422`: Validation Error
- `429`: Too Many Requests (Rate Limited)
- `500`: Internal Server Error

## Security Headers

The API includes security headers:
- `Strict-Transport-Security`: HSTS policy
- `Content-Security-Policy`: CSP policy
- `X-Frame-Options`: Clickjacking protection
- `X-Content-Type-Options`: MIME type sniffing protection
- `X-XSS-Protection`: Legacy XSS protection
- `Referrer-Policy`: Referrer information control