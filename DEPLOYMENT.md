# YatinVeda – Deployment Guide

> **Target**: Docker Compose on a single server (VPS / cloud VM). Suitable for 500–2000 concurrent users.

## Quick Summary

| Service | Port | Notes |
|---------|------|-------|
| nginx (proxy) | 80, 443 | HTTPS termination |
| backend (FastAPI) | 8000 (internal) | 4 uvicorn workers, auto-migrates on startup |
| frontend (Next.js) | 3000 (internal) | |
| postgres | 5432 (internal) | PostgreSQL 16 |
| redis | 6379 (internal) | Rate limit + cache |
| prometheus | 9090\* | Optional monitoring profile |
| grafana | 3001\* | Optional monitoring profile |

\* Only started with `--profile monitoring`

---

## Step 1 – Clone & Configure Environment

```powershell
# Clone (skip if already cloned)
git clone https://github.com/your-org/yatinveda.git
cd yatinveda

# Fill in secrets in .env
notepad .env
```

**Minimum required changes in `.env`:**

| Variable | Action |
|----------|--------|
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(64))"` |
| `POSTGRES_PASSWORD` | Set a strong password |
| `REDIS_PASSWORD` | Set a strong password |
| `MFA_ENCRYPTION_KEY` | Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `BACKEND_CORS_ORIGINS` | Set to your domain e.g. `https://yourdomain.com` |
| `NEXT_PUBLIC_API_BASE_URL` | Set to your domain e.g. `https://yourdomain.com` |
| `OPENAI_API_KEY` | Your OpenAI key (or leave blank to use `LLM_PROVIDER=local`) |
| `SENDGRID_API_KEY` | Your SendGrid key (or set `EMAIL_PROVIDER=mock` for no emails) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Your Razorpay credentials |

---

## Step 2 – Generate SSL Certificates

### Development / Self-Signed
```powershell
powershell -ExecutionPolicy Bypass -File scripts\generate-dev-certs.ps1
```

### Production (Let's Encrypt) — on a Linux server
```bash
# Install certbot
sudo apt install certbot
# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
# Copy to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
```

---

## Step 3 – Build & Start

```powershell
# Build images and start all services
docker compose up -d --build

# Watch logs
docker compose logs -f

# Check all containers are healthy
docker compose ps
```

---

## Step 4 – Run Database Migrations

Migrations are now run automatically by backend startup (`RUN_MIGRATIONS=true`).

Manual migration command (optional, for emergency/manual operation):

```powershell
docker compose exec backend alembic upgrade head
```

---

## Step 5 – Verify Everything Works

```powershell
# Backend health
Invoke-WebRequest https://localhost/api/v1/health -UseBasicParsing

# API docs
Invoke-WebRequest http://localhost:8000/docs -UseBasicParsing

# Frontend (via nginx HTTPS)
# Open https://localhost in browser (accept self-signed cert warning in dev)
```

---

## Step 6 – Create First Admin User

Use the API docs at `https://yourdomain.com/docs`:

1. `POST /api/v1/auth/register` — create an account
2. `POST /api/v1/admin/verify-practitioner` — promote to admin (use DB directly on first setup)

Or set up directly in the database:
```powershell
docker compose exec postgres psql -U yatinveda -d yatinveda -c "UPDATE users SET role='admin' WHERE email='your@email.com';"
```

---

## Optional: Monitoring Stack

```powershell
# Start with Prometheus + Grafana
docker compose --profile monitoring up -d

# Grafana: http://localhost:3001
# Username: admin  Password: (from GRAFANA_PASSWORD in .env)
```

The **YatinVeda FastAPI Overview** dashboard auto-provisions showing:
- Request rate (req/s)
- P95 latency
- 5xx error rate
- Auth login success/failure

---

## Useful Commands

```powershell
# Stop all services
docker compose down

# Stop and remove all data (CAUTION: deletes DB!)
docker compose down -v

# Restart just the backend
docker compose restart backend

# View backend logs
docker compose logs -f backend

# Show migration/startup logs
docker compose logs -f backend | Select-String -Pattern "entrypoint|alembic|Starting Uvicorn"

# Run backend tests
docker compose exec backend pytest -v --tb=short

# Check database
docker compose exec postgres psql -U yatinveda -d yatinveda -c "\dt"

# Flush Redis
docker compose exec redis redis-cli -a $env:REDIS_PASSWORD FLUSHALL
```

---

## Scaling Beyond 500 Users

The current setup handles 500–2000 users on a single server. To go further:

| Need | Solution |
|------|----------|
| More API throughput | Increase `--workers` in compose or add more backend replicas |
| Database scaling | Migrate to managed PostgreSQL (AWS RDS, Supabase, Neon) |
| Global CDN | Put Cloudflare in front for static assets |
| Kubernetes | Use `kubernetes-deployment-example.yaml` already in the repo |

---

## Security Checklist Before Going Live

- [ ] All `CHANGE_ME` values in `.env` replaced with real secrets
- [ ] `COOKIE_SECURE=true` and `COOKIE_SAMESITE=strict`
- [ ] `ENVIRONMENT=production`
- [ ] Real SSL certificate (not self-signed)
- [ ] `BACKEND_CORS_ORIGINS` set to your specific domain (not `*`)
- [ ] Firewall: only ports 80 and 443 open to public (5432, 6379, 8000, 3000 internal only)
- [ ] `REFRESH_TOKEN_BINDING=true`
- [ ] `RUN_MIGRATIONS=true` (or managed migration process in CI/CD)
