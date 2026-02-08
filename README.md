# YatinVeda

A hybrid, AI-assisted Vedic Astrology Intelligence Platform with comprehensive social features, AI guidance, and professional consultation booking.

## Features

### 🔐 Authentication & Security
- JWT-based authentication with cookie-based refresh tokens
- CSRF protection for secure cookie handling
- Token rotation and revocation
- Optional IP and User-Agent binding
- Comprehensive auth event logging

### 📊 Core Features
- **Birth Chart Management**: Create, read, update, delete birth charts with primary designation
- **Guru Booking System**: Book consultations with Vedic astrology experts
- **Payment Integration**: Razorpay real integration with HMAC-SHA256 verification & webhooks
- **Prescription Management**: Professional PDF generation with reportlab (prescriptions & charts)
- **AI Chat Assistant**: VedaMind AI with OpenAI/Anthropic/Ollama support
- **Two-Factor Authentication**: MFA with TOTP, backup codes, and trusted devices
- **Email Service**: Multi-provider (SendGrid/SMTP/Mock) with fallback chain

### 🌐 Social & Community
- **Community Posts**: Share insights, charts, and experiences
- **Comments & Likes**: Engage with nested comments and reactions
- **User Following**: Follow other users and build connections
- **Events**: Create and join community events and rituals
- **Notifications**: Stay updated with community activities

### 👤 User Management
- Extended user profiles with bio, avatar, and interests
- Password management and account deletion
- User statistics and activity tracking
- Profile customization and privacy settings

### 📈 Admin Features
- Token management and revocation
- Guru availability management
- Refund processing
- System cleanup operations

## Quick Start

### Prerequisites

- Docker Desktop (Windows)
- PowerShell (v5.1)

### Run with Docker Compose

```powershell
# Build and start backend, frontend, and proxy
docker compose up -d --build

# Tail logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f proxy

# Stop all
docker compose down
```

### Services

- Backend (FastAPI): `http://localhost:8000` (docs at `/docs`, health at `/health`)
- Frontend (Next.js): `http://localhost:3000`
- Proxy (Nginx): `http://localhost/` (routes `/api` → backend, `/` → frontend)

### API Endpoints

The backend exposes the following API groups:

- **`/api/v1/auth`** - Authentication (register, login, refresh, logout)
- **`/api/v1/charts`** - Birth chart CRUD operations
- **`/api/v1/profile`** - User profile management
- **`/api/v1/prescriptions`** - Prescription management with PDF generation
- **`/api/v1/chat`** - AI assistant for Vedic guidance
- **`/api/v1/community`** - Social features (posts, comments, likes, follows, events)
- **`/api/v1/guru-booking`** - Guru discovery, booking, and availability
- **`/api/v1/payments`** - Payment processing, wallet, and refunds
- **`/api/v1/admin`** - Admin operations

Visit `http://localhost:8000/docs` for interactive API documentation.

### Environment Variables

Backend accepts:

- `SECRET_KEY` (default: `development-secret`)
- `DATABASE_URL` (default: `sqlite:///./yatinveda.db`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `30`)
- `REFRESH_TOKEN_EXPIRE_DAYS` (default: `14`)
- `REFRESH_TOKEN_BINDING` (default: `false`)

Frontend accepts:

- `NEXT_PUBLIC_API_BASE_URL` (default: `http://localhost:8000`)

### Healthchecks

- Backend: `/health` (used by Compose)
- Frontend: `/` (used by Compose)

### VS Code Tasks

- Compose: Up (build)
- Compose: Logs Backend
- Compose: Logs Frontend
- Compose: Logs Proxy
- Compose: Down

## Development

### Backend Development

```powershell
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest -v
```

### Frontend Development

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Database Migrations

```powershell
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Testing

Current test coverage: **31 passing tests** (2.07s)

- Guru booking tests: 17 tests
- Payment tests: 14 tests

Run tests with:
```powershell
cd backend
pytest -v
```

## Architecture

### Technology Stack

- **Backend**: FastAPI 0.119.1, SQLAlchemy 2.0.36, Starlette 0.48.0
- **Frontend**: Next.js with TypeScript
- **Database**: SQLite (development), PostgreSQL recommended for production
- **Authentication**: JWT with httpOnly cookies, CSRF protection
- **Reverse Proxy**: Nginx with gzip, rate limiting, security headers
- **Containerization**: Docker with multi-stage builds
- **CI/CD**: GitHub Actions with pytest and Docker builds

### Project Structure

```
YatinVeda/
├── backend/              # FastAPI backend application
│   ├── api/             # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── middleware/      # Custom middleware
│   ├── tests/           # Test files and test resources
│   └── alembic/         # Database migrations
├── frontend/            # Next.js frontend application
│   ├── app/            # Next.js app directory
│   ├── components/     # React components
│   └── lib/            # Utility functions
├── nginx/              # Nginx reverse proxy configuration
├── docs/               # Project documentation
│   ├── api/           # API documentation
│   ├── guides/        # Feature guides and setup instructions
│   └── README.md      # Documentation index
├── samples/            # Sample code and usage examples
├── scripts/            # Utility scripts
└── docker-compose.yml  # Docker Compose configuration
```

## Security Features

- Cookie-based refresh tokens with httpOnly and SameSite flags
- CSRF token validation for protected endpoints
- Token rotation on refresh
- Optional IP and User-Agent binding
- Rate limiting (Nginx: 100 req/min, login: 10 req/min)
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options)
- Request correlation IDs for audit trails

## Project Status

✅ **Core Features** - Authentication, JWT, CSRF protection, MFA  
✅ **Social Features** - Community posts, comments, likes, follows, events  
✅ **Booking System** - Guru booking, availability management  
✅ **Payments** - Razorpay integration with webhooks  
✅ **AI Assistant** - VedaMind with OpenAI/Anthropic/Ollama  
✅ **PDF Generation** - Prescriptions & charts with QR codes  
✅ **Email Service** - Multi-provider with fallback chain  
✅ **HTTPS/TLS** - Production-ready SSL configuration  

**Overall: Production-Ready Platform**

## Documentation & Sample Code

### 📚 Documentation

All documentation has been organized in the [`docs/`](docs/) directory:

- **[docs/README.md](docs/README.md)** - Documentation index and quick navigation
- **[docs/api/API_DOCUMENTATION.md](docs/api/API_DOCUMENTATION.md)** - Complete API reference
- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Quick start guide
- **[docs/guides/](docs/guides/)** - Feature-specific guides:
  - Authentication & MFA
  - Database configuration
  - Email & PDF services
  - Monitoring & observability
  - SSL/TLS setup
  - VedaMind AI integration

### 💻 Sample Code

Ready-to-use examples in the [`samples/`](samples/) directory:

- **[sample_authentication.py](samples/sample_authentication.py)** - User registration, login, token management
- **[sample_mfa_flow.py](samples/sample_mfa_flow.py)** - Multi-factor authentication flows
- **[sample_booking.py](samples/sample_booking.py)** - Practitioner discovery and appointment booking
- **[sample_prescription.py](samples/sample_prescription.py)** - Prescription creation and PDF generation

See [samples/README.md](samples/README.md) for usage instructions.

## Notes

- Nginx adds gzip and basic per-IP rate limiting.
- Proxy trusts `X-Forwarded-*` headers; backend honors them via `ProxyHeadersMiddleware`.
- SQLite DB persisted via `backend_db` volume.
- All sensitive operations (MFA, payments, email) use encryption/HMAC for security.

