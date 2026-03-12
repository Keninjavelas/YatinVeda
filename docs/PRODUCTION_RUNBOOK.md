# YatinVeda — Production Runbook

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Startup & Shutdown](#2-startup--shutdown)
3. [Health Checks](#3-health-checks)
4. [Database Operations](#4-database-operations)
5. [Scaling](#5-scaling)
6. [Incident Response](#6-incident-response)
7. [Backup & Restore](#7-backup--restore)
8. [Monitoring & Alerting](#8-monitoring--alerting)
9. [Common Issues](#9-common-issues)
10. [Security Checklist](#10-security-checklist)

---

## 1. Architecture Overview

```
                     ┌──────────┐
                     │  Nginx   │ :80/:443 (TLS termination)
                     └────┬─────┘
                ┌─────────┴─────────┐
                │                   │
         ┌──────┴──────┐    ┌──────┴──────┐
         │  Frontend   │    │   Backend   │ ×3 replicas
         │  (Next.js)  │    │  (FastAPI)  │
         └─────────────┘    └──┬─────┬───┘
                               │     │
                        ┌──────┘     └──────┐
                   ┌────┴─────┐      ┌──────┴─────┐
                   │ Postgres │      │   Redis    │
                   │   (16)   │      │    (7)     │
                   └──────────┘      └────────────┘
```

**Tech Stack:**
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Frontend:** Next.js 14 (React 18), TypeScript
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Proxy:** Nginx (TLS termination, rate limiting)
- **Monitoring:** Prometheus + Grafana

---

## 2. Startup & Shutdown

### Docker Compose

```bash
# Start all services
docker compose up -d --build

# Graceful shutdown
docker compose down

# Restart a single service
docker compose restart backend

# View logs
docker compose logs -f backend
docker compose logs -f --tail=100 frontend
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/monitoring.yaml

# Scale backend
kubectl scale deployment backend -n yatinveda --replicas=5

# Rolling restart (zero-downtime)
kubectl rollout restart deployment/backend -n yatinveda

# Check rollout status
kubectl rollout status deployment/backend -n yatinveda
```

### Startup Order

1. PostgreSQL (wait for readiness)
2. Redis
3. Backend (runs `alembic upgrade head` via entrypoint.sh)
4. Frontend
5. Nginx/Ingress

---

## 3. Health Checks

| Endpoint | Expected | Purpose |
|---|---|---|
| `GET /api/v1/health` | `200 {"status": "healthy"}` | Liveness — app is running |
| `GET /api/v1/readiness` | `200` | Readiness — app can serve traffic (DB + Redis connected) |
| `GET /metrics` | Prometheus text | Metrics scrape endpoint |

```bash
# Quick health check
curl -sf https://yatinveda.com/api/v1/health | jq .

# Full readiness
curl -sf https://yatinveda.com/api/v1/readiness
```

---

## 4. Database Operations

### Migrations

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# View current migration version
docker compose exec backend alembic current

# Rollback one migration
docker compose exec backend alembic downgrade -1

# View migration history
docker compose exec backend alembic history --verbose
```

### Direct DB Access

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U user -d yatinveda

# Common diagnostic queries
SELECT count(*) FROM users;
SELECT count(*) FROM appointments WHERE status = 'pending';
SELECT pg_database_size('yatinveda');
```

### Connection Pool Tuning

Environment variables in `.env`:
```
DB_POOL_SIZE=10          # Concurrent connections per worker
DB_MAX_OVERFLOW=20       # Burst connections
DB_POOL_TIMEOUT=30       # Seconds to wait for connection
DB_POOL_RECYCLE=3600     # Recycle connections hourly
```

**Rule of thumb:** `DB_POOL_SIZE × num_workers < max_connections` (PostgreSQL default: 100).

---

## 5. Scaling

### Horizontal Scaling (Kubernetes)

HPA is preconfigured in `kubernetes/deployment.yaml`:
- **Backend:** 3–10 replicas, scales at 70% CPU / 80% memory
- **Frontend:** 2–6 replicas, scales at 75% CPU

```bash
# View current HPA status
kubectl get hpa -n yatinveda

# Manual override
kubectl scale deployment backend -n yatinveda --replicas=8
```

### Vertical Scaling (Docker Compose)

Resource limits are set in `docker-compose.yml`. To increase:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: "2.0"
        memory: 2G
```

### Beyond 2000 Concurrent Users

1. Upgrade PostgreSQL to a managed service (RDS, Cloud SQL, Azure Database)
2. Add read replicas for query-heavy workloads
3. Move Redis to a managed service (ElastiCache, Memorystore)
4. Enable Redis Cluster mode for cache-heavy workloads
5. Add CDN (CloudFront, Cloudflare) for frontend static assets
6. Consider adding a message queue (RabbitMQ, SQS) for async tasks (email, PDF generation)

---

## 6. Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|---|---|---|---|
| **P1 — Critical** | Service fully down or data loss | 15 min | Database corruption, all pods crash-looping |
| **P2 — High** | Major feature broken | 1 hour | Payments failing, auth broken |
| **P3 — Medium** | Degraded performance | 4 hours | Slow responses, cache miss spike |
| **P4 — Low** | Minor issue | Next business day | UI glitch, non-critical log errors |

### Triage Checklist

1. **Is the service reachable?** `curl /api/v1/health`
2. **Are pods running?** `kubectl get pods -n yatinveda` / `docker compose ps`
3. **Check logs:** `kubectl logs -l app=backend -n yatinveda --tail=200` / `docker compose logs backend --tail=200`
4. **Check metrics:** Grafana dashboard → request rate, error rate, latency
5. **Check DB:** `docker compose exec postgres pg_isready`
6. **Check Redis:** `docker compose exec redis redis-cli ping`

### Rollback

```bash
# GitHub Actions — trigger manual rollback
# Go to Actions → Deploy to Environments → Run workflow → Set rollback=true

# Manual Docker rollback
docker compose down
docker compose up -d  # Uses locally cached previous images

# Kubernetes rollback
kubectl rollout undo deployment/backend -n yatinveda
kubectl rollout undo deployment/frontend -n yatinveda
```

---

## 7. Backup & Restore

### Database Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U user -d yatinveda -Fc > backup_$(date +%Y%m%d_%H%M%S).dump

# Restore from backup
docker compose exec -i postgres pg_restore -U user -d yatinveda -c < backup_20240101_120000.dump
```

### Automated Backup (Cron)

Add to host crontab:
```cron
# Daily backup at 2 AM, keep 30 days
0 2 * * * docker compose exec -T postgres pg_dump -U user -d yatinveda -Fc > /backups/yatinveda_$(date +\%Y\%m\%d).dump && find /backups -name "yatinveda_*.dump" -mtime +30 -delete
```

### Recovery Targets

- **RPO (Recovery Point Objective):** 24 hours (daily backup)
- **RTO (Recovery Time Objective):** 1 hour (restore from backup + redeploy)

For lower RPO, enable PostgreSQL WAL archiving or use a managed database with point-in-time recovery.

---

## 8. Monitoring & Alerting

### Prometheus Alerts (defined in `monitoring/alerts.yml`)

| Alert | Condition | Severity |
|---|---|---|
| HighErrorRate | >5% of requests return 5xx for 5 min | Critical |
| HighLatency | p95 > 2 seconds for 5 min | Warning |
| RequestPileup | >100 active requests for 2 min | Warning |
| PodCrashLooping | >3 restarts in 1 hour | Critical |
| TargetDown | Scrape target unreachable for 3 min | Critical |
| DiskSpaceLow | <15% disk free for 10 min | Warning |
| HighMemoryUsage | >90% memory for 5 min | Warning |
| HighCPUUsage | >85% CPU for 10 min | Warning |

### Grafana Dashboards

Access at `https://grafana.yatinveda.com` (or `http://localhost:3001` in dev)

Key metrics to watch:
- Request rate (`http_requests_total`)
- Error rate (`http_errors_total`)
- Latency distribution (`http_request_duration_seconds`)
- Active connections (`http_active_requests`)
- DB connection count (`db_connections`)

### Log Aggregation

Backend logs are structured JSON (configured in `logging_config.py`). View with:
```bash
# Docker
docker compose logs backend --tail=500 | jq .

# Kubernetes
kubectl logs -l app=backend -n yatinveda --tail=500
```

---

## 9. Common Issues

### Backend won't start — "SECRET_KEY validation failed"
**Cause:** Production mode requires a non-default `SECRET_KEY`.
**Fix:** Set `SECRET_KEY` to a random 64+ character string in your environment.

### "Connection refused" to PostgreSQL
**Cause:** PostgreSQL not ready or wrong `DATABASE_URL`.
**Fix:** Check `docker compose ps postgres` and verify `DATABASE_URL` format:
`postgresql://user:password@postgres:5432/yatinveda`

### High latency / timeout on AI endpoints
**Cause:** LLM provider (OpenAI/Anthropic/Ollama) is slow or unreachable.
**Fix:** Check `LLM_PROVIDER` and API key. Switch to local Ollama for development.

### Rate limiting too aggressive
**Cause:** Default rate limits configured for single-user dev.
**Fix:** Tune rate limit tiers in `backend/middleware/rate_limit_tiers.py`.
Set `DISABLE_RATELIMIT=1` temporarily for debugging (never in production).

### CSRF token errors
**Cause:** Frontend and backend on different origins without proper CORS.
**Fix:** Ensure `BACKEND_CORS_ORIGINS` includes the frontend URL.
Check `CSRF_PROTECTION_ENABLED` is `true` and cookies are being sent with `credentials: 'include'`.

### Alembic migration conflictsw
**Cause:** Multiple developers created migrations from the same base.
**Fix:**
```bash
alembic merge heads -m "merge"
alembic upgrade head
```

---

## 10. Security Checklist

Before every production deployment, verify:

- [ ] `SECRET_KEY` is a unique, random string (not the default)
- [ ] `ENVIRONMENT=production` is set
- [ ] `COOKIE_SECURE=true` and `ENABLE_HTTPS=true`
- [ ] `CSRF_PROTECTION_ENABLED=true`
- [ ] `DISABLE_RATELIMIT=0`
- [ ] `RELOAD=false`
- [ ] Database credentials are not defaults
- [ ] TLS certificate is valid and not expired
- [ ] Container images scanned for vulnerabilities (Trivy in CI)
- [ ] Dependencies scanned (`pip-audit`, `npm audit`)
- [ ] CORS origins restricted to production domains only
- [ ] Redis is not exposed externally (bind to internal network)
- [ ] PostgreSQL is not exposed externally
- [ ] Grafana admin password changed from default `CHANGE_ME_GRAFANA_PASSWORD`
- [ ] All `CHANGE_ME` values in Kubernetes secrets are replaced
