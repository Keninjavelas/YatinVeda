<div align="center">

# 🌟 YatinVeda

### *Ancient Wisdom Meets Modern Intelligence*

**A comprehensive AI-powered Vedic Astrology platform combining traditional wisdom with cutting-edge technology**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.1-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[🚀 Quick Start](#-quick-start) • [📖 Documentation](docs/) • [💻 API Docs](#-api-documentation) • [🤝 Contributing](CONTRIBUTING.md)

---

</div>

## 🎯 Overview

YatinVeda is a production-ready, full-stack platform that bridges ancient Vedic astrology wisdom with modern AI technology. Built for practitioners, enthusiasts, and seekers, it offers professional-grade tools for birth chart analysis, AI-powered guidance, community engagement, and professional consultations.

### ✨ What Makes YatinVeda Special

- 🔮 **AI-Powered Insights**: VedaMind AI assistant with support for OpenAI, Anthropic, and Ollama
- 🎨 **Modern Architecture**: Microservices-based design with FastAPI, Next.js, and Docker
- 🔐 **Enterprise Security**: JWT authentication, MFA, CSRF protection, and rate limiting
- 📊 **Professional Tools**: PDF prescription generation, payment integration, and booking system
- 🌐 **Community Driven**: Social features with posts, comments, events, and user connections
- 📱 **Production Ready**: Comprehensive testing, monitoring, and deployment guides


---

## 🚀 Features

<table>
<tr>
<td width="50%">

### 🔐 Security & Authentication

- **Multi-Factor Authentication (MFA)** with TOTP and backup codes
- **JWT-based Authentication** with secure cookie handling
- **CSRF Protection** for all state-changing operations
- **Token Rotation** and automatic revocation
- **IP/User-Agent Binding** for enhanced security
- **Comprehensive Audit Logging** for all auth events

### 📊 Core Platform Features

- **Birth Chart Management** - CRUD operations with primary chart designation
- **VedaMind AI Assistant** - Vedic wisdom powered by LLMs
- **Prescription System** - Professional PDF generation with QR codes
- **Payment Gateway** - Razorpay integration with webhook support
- **Email Service** - Multi-provider fallback chain (SendGrid/SMTP)
- **PDF Generation** - Charts and prescriptions with custom branding

</td>
<td width="50%">

### 🌐 Social & Community

- **Community Posts** - Share insights and experiences
- **Nested Comments** - Deep engagement with threaded discussions
- **User Following** - Build your network of practitioners and enthusiasts
- **Community Events** - Create and join Vedic rituals and gatherings
- **Reaction System** - Likes and engagement tracking
- **Real-time Notifications** - Stay updated on community activities

### 👥 User Management

- **Extended Profiles** - Bio, avatar, interests, and specializations
- **Role-Based Access** - User, Practitioner, and Admin roles
- **Profile Privacy** - Customizable visibility settings
- **Activity Tracking** - Statistics and engagement metrics
- **Account Management** - Password reset, email verification, deletion

</td>
</tr>
</table>

### 🏥 Professional Services

- **Guru Booking System** - Schedule consultations with verified practitioners
- **Availability Management** - Real-time calendar and slot management
- **Payment Processing** - Secure transactions with automatic refunds
- **Wallet System** - Credit management and transaction history
- **Rating & Reviews** - Build trust through community feedback

### 📈 Admin & Operations

- **Token Management** - Revoke and monitor active sessions
- **User Verification** - Approve practitioner applications
- **Payment Administration** - Process refunds and handle disputes
- **System Analytics** - Monitor platform health and usage
- **Cleanup Operations** - Automated maintenance tasks


---

## 📋 Roadmap & Remaining Tasks

### 🔴 High Priority

- [ ] **Administrator Alert System** - Implement certificate expiry alerts to admin dashboard
- [ ] **Frontend Test Coverage** - Expand Jest/React Testing Library test suite (currently backend-focused)
- [ ] **PostgreSQL Migration** - Production deployment guide for PostgreSQL (currently using SQLite)
- [ ] **WebSocket Support** - Real-time notifications and chat features
- [ ] **Mobile Responsiveness** - Enhanced mobile UI/UX optimization

### 🟡 Medium Priority

- [ ] **Advanced Analytics Dashboard** - Practitioner performance metrics and insights
- [ ] **Advanced Search** - Elasticsearch integration for faster queries
- [ ] **Video Consultations** - WebRTC integration for online sessions
- [ ] **Astrological Calculations** - Native chart calculation engine (currently relies on external data)
- [ ] **Stripe Integration** - Add Stripe payment gateway for international markets

### 🟢 Nice to Have

- [ ] **Mobile Apps** - React Native iOS/Android applications
- [ ] **Kubernetes Deployment** - Production-grade k8s manifests (example provided)
- [ ] **API Rate Limit Tiers** - Tiered pricing with different rate limits
- [ ] **Social Media Integration** - Share charts and insights on social platforms
- [ ] **Advanced Remedies** - Expanded remedy recommendations with tracking

### ✅ Completed Features

<details>
<summary>View completed milestones</summary>

- ✅ Core authentication with JWT and refresh tokens
- ✅ Multi-factor authentication (MFA) with TOTP
- ✅ Community features (posts, comments, likes, follows, events)
- ✅ Booking system with availability management
- ✅ Payment integration with Razorpay
- ✅ PDF generation for prescriptions and charts
- ✅ Email service with multi-provider support
- ✅ AI assistant (VedaMind) with multiple LLM providers
- ✅ HTTPS/TLS configuration guides
- ✅ Docker containerization and docker-compose setup
- ✅ Comprehensive security middleware (CSRF, rate limiting, security headers)
- ✅ Database migrations with Alembic
- ✅ API documentation with OpenAPI/Swagger
- ✅ Basic monitoring setup (Prometheus/Grafana guide)

</details>

---

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Download |
|------------|---------|----------|
| Docker Desktop | Latest | [Download](https://www.docker.com/products/docker-desktop) |
| PowerShell | 5.1+ | Pre-installed on Windows |
| Git | Latest | [Download](https://git-scm.com/) |

### ⚡ One-Command Setup

```powershell
# Clone and start the entire platform
git clone https://github.com/Keninjavelas/YatinVeda.git
cd YatinVeda
docker compose up -d --build
```

### 🎯 Access Your Platform

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Next.js web application |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger documentation |
| **Proxy** | http://localhost | Nginx reverse proxy |
| **Health Check** | http://localhost:8000/health | Backend health status |

### 🔧 Management Commands

```powershell
# View logs
docker compose logs -f backend   # Backend logs
docker compose logs -f frontend  # Frontend logs
docker compose logs -f proxy     # Nginx logs

# Restart services
docker compose restart backend
docker compose restart frontend

# Stop all services
docker compose down

# Clean rebuild
docker compose down -v  # Remove volumes
docker compose up -d --build
```

### 🎨 VS Code Integration

Pre-configured tasks available in VS Code:

- `Compose: Up (build)` - Start all services
- `Compose: Logs Backend` - Stream backend logs
- `Compose: Logs Frontend` - Stream frontend logs
- `Compose: Logs Proxy` - Stream proxy logs
- `Compose: Down` - Stop all services

Press `Ctrl+Shift+P` → `Tasks: Run Task` to access these commands.

---

## 📡 API Documentation

### Available Endpoints

| Endpoint Group | Path | Description |
|---------------|------|-------------|
| **Authentication** | `/api/v1/auth` | Register, login, refresh, logout, MFA |
| **Birth Charts** | `/api/v1/charts` | CRUD operations for birth charts |
| **User Profiles** | `/api/v1/profile` | Profile management and customization |
| **Prescriptions** | `/api/v1/prescriptions` | PDF prescriptions and management |
| **AI Assistant** | `/api/v1/chat` | VedaMind AI for Vedic guidance |
| **Community** | `/api/v1/community` | Posts, comments, likes, follows, events |
| **Bookings** | `/api/v1/guru-booking` | Practitioner discovery and scheduling |
| **Payments** | `/api/v1/payments` | Razorpay integration, wallets, refunds |
| **Admin** | `/api/v1/admin` | Administrative operations |

### 🔍 Interactive Documentation

Visit **http://localhost:8000/docs** for:
- Complete API reference with request/response schemas
- "Try it out" functionality for testing endpoints
- Authentication testing with bearer tokens
- Schema definitions and examples

### ⚙️ Environment Configuration

<details>
<summary><b>Backend Environment Variables</b></summary>

```bash
# Security
SECRET_KEY=your-secret-key-here          # Default: development-secret
ALGORITHM=HS256                           # JWT algorithm

# Database
DATABASE_URL=sqlite:///./yatinveda.db    # Default: SQLite (use PostgreSQL for production)

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30            # Default: 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS=14              # Default: 14 days
REFRESH_TOKEN_BINDING=false               # IP/UA binding (true for production)

# MFA
MFA_ENCRYPTION_KEY=your-fernet-key-here  # For TOTP secret encryption

# Email Service
EMAIL_PROVIDER=sendgrid                   # Options: sendgrid, smtp, mock
SENDGRID_API_KEY=your-key-here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password

# AI Assistant
AI_PROVIDER=openai                        # Options: openai, anthropic, ollama
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
OLLAMA_BASE_URL=http://localhost:11434

# Payment Gateway
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

</details>

<details>
<summary><b>Frontend Environment Variables</b></summary>

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Optional: Analytics, monitoring, etc.
NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

</details>


---

## 💻 Development

### Local Development Setup

<details>
<summary><b>Backend Development</b></summary>

```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests with coverage
pytest -v --cov=. --cov-report=html

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# View database migrations
alembic history
```

**Key Directories:**
- `api/` - FastAPI route handlers
- `models/` - SQLAlchemy ORM models
- `schemas/` - Pydantic validation schemas
- `services/` - Business logic layer
- `middleware/` - Custom middleware (security, logging)
- `tests/` - Pytest test suite

</details>

<details>
<summary><b>Frontend Development</b></summary>

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install

# Start development server
npm run dev
# or
yarn dev

# Build for production
npm run build
npm start

# Run tests
npm test
# or
yarn test

# Lint code
npm run lint
```

**Key Directories:**
- `app/` - Next.js 14 app directory (pages and layouts)
- `components/` - Reusable React components
- `lib/` - Utility functions and helpers
- `public/` - Static assets

</details>

### Database Management

```powershell
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (development only!)
alembic downgrade base
alembic upgrade head
```


---

## 🧪 Testing

### Current Test Coverage

```
✅ Backend: 31+ passing tests (2.07s runtime)
📊 Coverage: Core features well-tested
🎯 Focus Areas: Authentication, Payments, Bookings
```

**Test Breakdown:**
- **Guru Booking Tests**: 17 tests (availability, booking flow, cancellation)
- **Payment Tests**: 14 tests (Razorpay integration, webhooks, refunds)
- **Security Tests**: Authentication, CSRF, rate limiting, token validation
- **Integration Tests**: Full API endpoint coverage

### Running Tests

```powershell
# Run all tests
cd backend
pytest -v

# Run with coverage report
pytest -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_guru_booking.py -v

# Run tests matching pattern
pytest -k "payment" -v

# Run tests with output
pytest -v -s

# Generate coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures
├── test_auth.py            # Authentication tests
├── test_guru_booking.py    # Booking system tests
├── test_payments.py        # Payment integration tests
├── test_security_*.py      # Security middleware tests
└── test-resources/         # Test fixtures and data
```

---

## 🛠️ Troubleshooting & Deployment Issues

### Common Deployment Errors

<details>
<summary><b>Docker Container Issues</b></summary>

#### Error: "Port already in use"
```bash
Error: bind: address already in use
```

**Solution:**
```powershell
# Find process using the port
netstat -ano | findstr :8000
# Kill the process
taskkill /PID <process_id> /F

# Or use different ports in docker-compose.yml
ports:
  - "8001:8000"  # Change host port
```

#### Error: "Cannot connect to Docker daemon"
```bash
error during connect: This error may indicate that the docker daemon is not running
```

**Solution:**
- Ensure Docker Desktop is running
- Restart Docker Desktop
- Check Docker Desktop settings → Resources → WSL integration (Windows)

#### Error: "Image build failed"
```bash
ERROR [internal] load metadata for docker.io/library/python:3.9-slim
```

**Solution:**
```powershell
# Clear Docker cache and rebuild
docker system prune -a
docker compose build --no-cache
docker compose up -d
```

</details>

<details>
<summary><b>Database Migration Errors</b></summary>

#### Error: "Target database is not up to date"
```bash
FAILED: Target database is not up to date.
```

**Solution:**
```powershell
cd backend
# Check current revision
alembic current

# Apply all migrations
alembic upgrade head

# If stuck, check migration history
alembic history
```

#### Error: "Can't locate revision identified by"
```bash
sqlalchemy.exc.InvalidRequestError: Can't locate revision identified by 'xxxxx'
```

**Solution:**
```powershell
# Reset database (development only!)
rm yatinveda.db
alembic stamp head
alembic upgrade head
```

#### Error: "Multiple head revisions are present"
```bash
FAILED: Multiple head revisions are present
```

**Solution:**
```powershell
# Merge multiple heads
alembic merge heads -m "merge multiple heads"
alembic upgrade head
```

</details>

<details>
<summary><b>Backend API Errors</b></summary>

#### Error: "ModuleNotFoundError"
```python
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```powershell
cd backend
pip install -r requirements.txt
# Or reinstall
pip install --upgrade --force-reinstall -r requirements.txt
```

#### Error: "SECRET_KEY not found"
```bash
KeyError: 'SECRET_KEY'
```

**Solution:**
```powershell
# Create .env file
cp .env.example .env
# Edit .env and set SECRET_KEY
# Generate secure key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Error: "Database connection failed"
```bash
sqlalchemy.exc.OperationalError: unable to open database file
```

**Solution:**
```powershell
# Ensure database directory exists
mkdir -p backend
# Check DATABASE_URL in .env
# Verify file permissions
# For PostgreSQL, check connection string format
DATABASE_URL=postgresql://user:password@localhost:5432/yatinveda
```

#### Error: "CORS policy blocked"
```bash
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**
```python
# In backend/main.py, verify CORS settings:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

</details>

<details>
<summary><b>Frontend Build Errors</b></summary>

#### Error: "npm ERR! code ELIFECYCLE"
```bash
npm ERR! code ELIFECYCLE
npm ERR! errno 1
```

**Solution:**
```powershell
cd frontend
# Clear cache
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### Error: "Module not found: Can't resolve"
```bash
Module not found: Error: Can't resolve '@/components/...'
```

**Solution:**
```powershell
# Check tsconfig.json paths configuration
# Ensure files exist in correct directory
# Restart dev server
npm run dev
```

#### Error: "NEXT_PUBLIC_API_BASE_URL is undefined"
```bash
TypeError: Cannot read property 'NEXT_PUBLIC_API_BASE_URL' of undefined
```

**Solution:**
```powershell
# Create .env.local in frontend directory
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
# Restart dev server
```

</details>

<details>
<summary><b>Production Deployment Issues</b></summary>

#### SSL/TLS Certificate Errors
```bash
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
- Use Let's Encrypt for free SSL certificates
- Follow [HTTPS/TLS Configuration Guide](docs/guides/HTTPS_TLS_CONFIGURATION_GUIDE.md)
- For development, use self-signed certificates: `scripts/generate-dev-certificates.bat`

#### Error: "502 Bad Gateway" (Nginx)
```bash
nginx: [emerg] host not found in upstream "backend"
```

**Solution:**
```powershell
# Check backend service is running
docker compose logs backend

# Verify nginx.conf upstream configuration
upstream backend {
    server backend:8000;  # Must match service name in docker-compose.yml
}

# Restart nginx
docker compose restart proxy
```

#### Performance Issues in Production
**Symptoms:** Slow response times, high memory usage

**Solution:**
```powershell
# Enable production optimizations in .env:
DEBUG=false
ACCESS_TOKEN_EXPIRE_MINUTES=15  # Shorter expiry
REFRESH_TOKEN_BINDING=true      # IP binding

# Use PostgreSQL instead of SQLite
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Enable Redis for caching
REDIS_URL=redis://localhost:6379/0

# Configure Nginx caching and compression
# See nginx/nginx.conf

# Monitor with Prometheus/Grafana
# Follow: docs/guides/PROMETHEUS_GRAFANA_MONITORING_GUIDE.md
```

</details>

### Pre-Deployment Checklist

Before deploying to production, ensure:

```bash
✅ Environment Variables
  - SECRET_KEY set to cryptographically random value
  - DATABASE_URL pointing to PostgreSQL (not SQLite)
  - Email provider credentials configured
  - Payment gateway keys (Razorpay) set
  - AI API keys configured (OpenAI/Anthropic)

✅ Security
  - REFRESH_TOKEN_BINDING=true
  - HTTPS/SSL certificates installed
  - CORS origins configured (no wildcards)
  - Rate limiting enabled via Redis
  - Security headers configured in Nginx

✅ Database
  - All migrations applied (alembic upgrade head)
  - Database backups configured
  - Connection pooling optimized

✅ Monitoring & Logging
  - Log aggregation setup (ELK, CloudWatch, etc.)
  - Application monitoring configured
  - Error tracking enabled (Sentry, etc.)
  - Health check endpoints working

✅ Performance
  - Redis caching enabled
  - Nginx gzip compression enabled
  - Static assets optimized
  - Database indexes created

✅ Testing
  - All tests passing (pytest)
  - Load testing completed
  - Security scanning performed
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs:** `docker compose logs -f [service-name]`
2. **Review Documentation:** See [docs/](docs/) for detailed guides
3. **Search Issues:** Check [GitHub Issues](https://github.com/yourusername/YatinVeda/issues)
4. **Ask Community:** Open a [Discussion](https://github.com/yourusername/YatinVeda/discussions)
5. **Report Bugs:** Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)

---

## 🏗️ Architecture & Technology

### Technology Stack

<table>
<tr>
<td width="50%">

#### Backend Technologies

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | FastAPI | 0.119.1 |
| **ORM** | SQLAlchemy | 2.0.36 |
| **ASGI Server** | Uvicorn | Latest |
| **Database** | SQLite / PostgreSQL | - |
| **Authentication** | JWT (python-jose) | Latest |
| **MFA** | PyOTP | Latest |
| **PDF Generation** | ReportLab | Latest |
| **Email** | SendGrid / SMTP | - |
| **Payments** | Razorpay | Latest |
| **AI/LLM** | OpenAI / Anthropic | Latest |

</td>
<td width="50%">

#### Frontend Technologies

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | Next.js | 14+ |
| **Language** | TypeScript | 5.0+ |
| **UI Library** | React | 18+ |
| **Styling** | Tailwind CSS / CSS Modules | - |
| **State Management** | React Context / Hooks | - |
| **HTTP Client** | Fetch API | Native |
| **Testing** | Jest / RTL | Latest |

</td>
</tr>
</table>

#### Infrastructure & DevOps

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Reverse Proxy** | Nginx | Rate limiting, HTTPS, routing |
| **Containerization** | Docker / Docker Compose | Service orchestration |
| **Database Migrations** | Alembic | Version-controlled schema changes |
| **Monitoring** | Prometheus / Grafana | Metrics and alerting |
| **Caching** | Redis | Session storage and rate limiting |
| **CI/CD** | GitHub Actions | Automated testing and deployment |

### Project Structure

```
YatinVeda/
├── 📁 backend/                    # FastAPI Backend Application
│   ├── 📁 api/
│   │   └── 📁 v1/                # API version 1 endpoints
│   │       ├── auth.py           # Authentication & MFA
│   │       ├── charts.py         # Birth chart management
│   │       ├── chat.py           # AI assistant (VedaMind)
│   │       ├── community.py      # Social features
│   │       ├── guru_booking.py   # Booking system
│   │       ├── payments.py       # Razorpay integration
│   │       └── prescriptions.py  # PDF prescriptions
│   ├── 📁 models/                # SQLAlchemy ORM models
│   ├── 📁 schemas/               # Pydantic validation schemas
│   ├── 📁 services/              # Business logic layer
│   ├── 📁 middleware/            # Custom middleware
│   │   ├── security_headers.py  # Security headers
│   │   ├── rate_limiter.py      # Rate limiting
│   │   └── csrf.py              # CSRF protection
│   ├── 📁 modules/               # Feature modules
│   │   ├── mfa.py               # MFA implementation
│   │   ├── email_service.py     # Email provider abstraction
│   │   ├── pdf_generator.py     # PDF creation
│   │   └── certificate_manager.py # SSL/TLS management
│   ├── 📁 tests/                 # Pytest test suite
│   ├── 📁 alembic/               # Database migrations
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   └── requirements.txt          # Python dependencies
│
├── 📁 frontend/                   # Next.js Frontend Application
│   ├── 📁 app/                   # Next.js 14 app directory
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Home page
│   │   └── (auth)/              # Auth route group
│   ├── 📁 components/            # React components
│   │   ├── MFASetup.tsx         # MFA setup wizard
│   │   ├── MFAVerify.tsx        # MFA verification
│   │   └── ...                  # Other components
│   ├── 📁 lib/                   # Utilities and helpers
│   ├── 📁 public/                # Static assets
│   ├── package.json              # Node dependencies
│   └── tsconfig.json             # TypeScript config
│
├── 📁 nginx/                      # Nginx Configuration
│   ├── nginx.conf               # Main config with rate limiting
│   └── ssl/                     # SSL certificates (production)
│
├── 📁 docs/                       # Documentation
│   ├── 📁 api/                   # API documentation
│   │   └── API_DOCUMENTATION.md # Complete API reference
│   ├── 📁 guides/                # Feature-specific guides (15 guides)
│   │   ├── AUTH.md              # Authentication guide
│   │   ├── MFA_GUIDE.md         # MFA setup and usage
│   │   ├── PDF_GENERATION_GUIDE.md
│   │   ├── EMAIL_SERVICE_GUIDE.md
│   │   └── ...                  # More guides
│   ├── README.md                # Documentation index
│   └── QUICK_REFERENCE.md       # Quick start guide
│
├── 📁 samples/                    # Sample Code & Examples
│   ├── sample_authentication.py  # Auth flow examples
│   ├── sample_mfa_flow.py       # MFA implementation
│   ├── sample_booking.py        # Booking system usage
│   ├── sample_prescription.py   # Prescription management
│   └── README.md                # Usage instructions
│
├── 📁 scripts/                    # Utility Scripts
│   └── generate-dev-certificates.bat
│
├── docker-compose.yml            # Multi-container orchestration
├── docker-compose-ssl.yml        # SSL-enabled compose
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── CONTRIBUTING.md               # Contribution guidelines
```

---

## 🔒 Security Features

### Authentication & Authorization

- **JWT-based Authentication** with RS256/HS256 algorithms
- **Refresh Token Rotation** with automatic revocation
- **HttpOnly Cookies** for secure token storage
- **CSRF Protection** with double-submit cookie pattern
- **Multi-Factor Authentication (MFA)** with TOTP (Google Authenticator compatible)
- **Backup Codes** for account recovery
- **Trusted Device Management** with IP/User-Agent tracking
- **Role-Based Access Control (RBAC)** - User, Practitioner, Admin roles

### Application Security

| Feature | Implementation | Status |
|---------|---------------|---------|
| **Rate Limiting** | Redis-backed with configurable limits | ✅ Active |
| **Security Headers** | CSP, X-Frame-Options, HSTS, etc. | ✅ Active |
| **SQL Injection Protection** | SQLAlchemy ORM with parameterized queries | ✅ Active |
| **XSS Protection** | Input sanitization and output encoding | ✅ Active |
| **CORS Configuration** | Strict origin validation | ✅ Active |
| **Request Validation** | Pydantic schemas for all inputs | ✅ Active |
| **Audit Logging** | Correlation IDs and event tracking | ✅ Active |
| **Password Hashing** | bcrypt with configurable work factor | ✅ Active |
| **MFA Encryption** | Fernet symmetric encryption for TOTP secrets | ✅ Active |
| **Payment Security** | HMAC-SHA256 signature verification | ✅ Active |

### Security Best Practices

```python
# All sensitive operations are protected
@rate_limit(max_requests=5, window=60)  # Rate limiting
@require_csrf_token  # CSRF protection
@require_mfa  # MFA required for sensitive operations
async def sensitive_endpoint():
    pass
```

### Production Security Checklist

- [ ] Change `SECRET_KEY` to cryptographically random value
- [ ] Enable `REFRESH_TOKEN_BINDING=true` for production
- [ ] Switch to PostgreSQL or MySQL (no SQLite in production)
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure proper CORS origins (no wildcards)
- [ ] Set up Redis for distributed rate limiting
- [ ] Enable comprehensive logging and monitoring
- [ ] Regular security audits and dependency updates
- [ ] Implement backup and disaster recovery procedures
- [ ] Configure firewall rules and network security groups


---

## 📚 Documentation & Resources

### 📖 Complete Documentation

Visit the [`docs/`](docs/) directory for comprehensive guides:

| Category | Location | Description |
|----------|----------|-------------|
| **Quick Start** | [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | Rapid setup guide |
| **API Reference** | [docs/api/API_DOCUMENTATION.md](docs/api/API_DOCUMENTATION.md) | Complete REST API docs |
| **Feature Guides** | [docs/guides/](docs/guides/) | 15+ implementation guides |
| **Sample Code** | [samples/](samples/) | Working examples for all major features |

### 🎓 Feature-Specific Guides

#### Security & Authentication
- [Authentication Guide](docs/guides/AUTH.md) - JWT, cookies, sessions
- [MFA Guide](docs/guides/MFA_GUIDE.md) - Multi-factor authentication setup
- [MFA Flows](docs/guides/MFA_FLOWS.md) - Workflow diagrams
- [Frontend MFA Integration](docs/guides/MFA_FRONTEND_INTEGRATION_GUIDE.md)
- [HTTPS/TLS Configuration](docs/guides/HTTPS_TLS_CONFIGURATION_GUIDE.md)
- [Cookie Integration](docs/guides/COOKIE_INTEGRATION.md)
- [Protected Routes](docs/guides/PROTECTED_ROUTES.md)

#### Data & Infrastructure
- [Database Report](docs/guides/DATABASE_REPORT.md) - Schema and relationships
- [PostgreSQL Migration](docs/guides/POSTGRESQL_MIGRATION_GUIDE.md) - Production setup
- [Redis Tracing Setup](docs/guides/REDIS_TRACING_SETUP.md) - Caching layer

#### Services & Features
- [Email Service Guide](docs/guides/EMAIL_SERVICE_GUIDE.md) - Multi-provider setup
- [PDF Generation Guide](docs/guides/PDF_GENERATION_GUIDE.md) - Prescription PDFs
- [VedaMind Guide](docs/guides/VEDAMIND_GUIDE.md) - AI assistant integration
- [AI Assistant Guide](docs/guides/AI_ASSISTANT_GUIDE.md) - LLM configuration

#### Monitoring & Operations
- [Prometheus & Grafana Guide](docs/guides/PROMETHEUS_GRAFANA_MONITORING_GUIDE.md)

### 💻 Sample Code Examples

Practical, runnable examples in the [`samples/`](samples/) directory:

```python
# Authentication Example - samples/sample_authentication.py
response = login_user(email="user@example.com", password="secure123")
profile = get_user_profile(response["access_token"])

# MFA Example - samples/sample_mfa_flow.py
mfa_setup = enable_mfa(access_token)
verify_mfa_setup(access_token, totp_code)

# Booking Example - samples/sample_booking.py
practitioners = get_practitioners(access_token, specialty="ayurveda")
booking = create_booking(access_token, practitioner_id, appointment_time)

# Prescription Example - samples/sample_prescription.py
prescription = create_prescription(access_token, patient_id, diagnosis, medicines)
pdf = get_prescription_pdf(access_token, prescription_id)
```

See [samples/README.md](samples/README.md) for detailed usage instructions.

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's bug fixes, new features, documentation improvements, or sample code, your help is appreciated.

### How to Contribute

1. **Fork the Repository** - Create your own fork on GitHub
2. **Clone & Setup** - Follow the [development setup](#-development) instructions
3. **Create a Branch** - `git checkout -b feature/your-feature-name`
4. **Make Changes** - Implement your feature or fix
5. **Write Tests** - Ensure your changes are tested
6. **Update Docs** - Keep documentation in sync with code
7. **Submit PR** - Open a pull request with a clear description

### Contribution Guidelines

- Follow the existing code style (PEP 8 for Python, ESLint for TypeScript)
- Write meaningful commit messages
- Add tests for new features
- Update documentation for API changes
- Keep PRs focused on a single concern

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - For the amazing web framework
- **Next.js** - For the powerful React framework
- **OpenAI** - For AI capabilities
- **Vedic Astrology Community** - For ancient wisdom and guidance
- **Contributors** - Thank you to everyone who has contributed!

---

## 📞 Support & Contact

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/YatinVeda/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/YatinVeda/discussions)

---

<div align="center">

**Made with ❤️ by the YatinVeda Team**

*Bridging Ancient Wisdom with Modern Technology*

[⬆ Back to Top](#-yatinveda)

</div>

