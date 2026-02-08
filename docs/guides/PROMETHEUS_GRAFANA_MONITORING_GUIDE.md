# Monitoring Setup Guide - Prometheus & Grafana

## Overview

This guide explains how to set up comprehensive monitoring for the YatinVeda platform using Prometheus for metrics collection and Grafana for visualization and alerting.

## Components

### 1. Prometheus Metrics Collection

The application includes built-in Prometheus-compatible metrics:

- HTTP request counts and durations
- Active request tracking
- Database connection metrics
- Cache hit/miss ratios
- Error rates and status codes
- System resource usage

### 2. Metrics Endpoint

The application exposes metrics at `/metrics` endpoint in Prometheus format.

## Docker Compose Setup

Update `docker-compose.yml` to include monitoring services:

```yaml
version: "3.9"
services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: yatinveda-postgres
    environment:
      POSTGRES_DB: yatinveda_db
      POSTGRES_USER: yatinveda_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-StrongPassword123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yatinveda_user -d yatinveda_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis for session storage and caching
  redis:
    image: redis:7-alpine
    container_name: yatinveda-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped

  # Backend service
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: yatinveda-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://yatinveda_user:${POSTGRES_PASSWORD:-StrongPassword123}@postgres:5432/yatinveda_db
      - ENVIRONMENT=production
      - DB_POOL_SIZE=20
      - DB_MAX_OVERFLOW=30
      - DB_POOL_TIMEOUT=30
      - DB_POOL_RECYCLE=3600
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - LLM_PROVIDER=${LLM_PROVIDER:-openai}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - COOKIE_SECURE=true
      - REFRESH_TOKEN_BINDING=true
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Frontend service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: yatinveda-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://api.yatinveda.com
    depends_on:
      - backend
    restart: unless-stopped

  # Prometheus Server
  prometheus:
    image: prom/prometheus:latest
    container_name: yatinveda-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana-enterprise
    container_name: yatinveda-grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

  # Node Exporter (for system metrics)
  node_exporter:
    image: prom/node-exporter:latest
    container_name: yatinveda-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

  # Nginx proxy
  proxy:
    image: nginx:alpine
    container_name: yatinveda-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

## Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node_exporter:9100']

  - job_name: 'yatinveda-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s
```

## Grafana Configuration

Create `monitoring/datasources/datasource.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    orgId: 1
    url: http://prometheus:9090
    password: ""
    user: ""
    database: ""
    basicAuth: false
    basicAuthUser: ""
    basicAuthPassword: ""
    withCredentials: false
    isDefault: true
    version: 1
    editable: true
```

Create `monitoring/dashboards/dashboard.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'YatinVeda Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

## Sample Grafana Dashboard

Create `monitoring/dashboards/yatinveda-dashboard.json`:

```json
{
  "dashboard": {
    "id": null,
    "title": "YatinVeda Application Dashboard",
    "tags": ["yatinveda", "fastapi", "backend"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests Total",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(http_requests_total)",
            "legendFormat": "Total Requests"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Active Requests",
        "type": "singlestat",
        "targets": [
          {
            "expr": "http_active_requests",
            "legendFormat": "Active Requests"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
      },
      {
        "id": 4,
        "title": "Average Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95 Response Time"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 5,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_errors_total[5m])",
            "legendFormat": "Errors per Second"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 6,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "db_connections",
            "legendFormat": "Connections"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 7,
        "title": "Cache Hit Ratio",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))",
            "legendFormat": "Hit Ratio"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "timepicker": {},
    "templating": {
      "list": []
    },
    "annotations": {
      "list": []
    },
    "refresh": "5s",
    "schemaVersion": 17,
    "version": 0
  }
}
```

## Alerting Rules

Create `monitoring/alerts/rules.yml`:

```yaml
groups:
- name: yatinveda_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_errors_total[5m]) > 10
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "More than 10 errors per minute for the last 2 minutes"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "P95 response time is greater than 2 seconds"

  - alert: ServiceDown
    expr: up{job="yatinveda-backend"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "YatinVeda backend service is not responding"
```

## Environment Variables

Add to `.env` file:

```env
# Monitoring Configuration
GRAFANA_ADMIN_PASSWORD=your_secure_password

# Database Configuration for Production
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_production_secret_key
OPENAI_API_KEY=your_openai_api_key
```

## Starting the Monitoring Stack

1. Create the required directories:
```bash
mkdir -p monitoring/{dashboards,datasources,alerts}
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the services:
   - Application: https://localhost
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001 (login with admin/your_password)
   - Node Exporter: http://localhost:9100

## Metrics Collected

### HTTP Metrics
- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: Request duration histogram
- `http_active_requests`: Number of currently active requests
- `http_errors_total`: Total HTTP errors by method, endpoint, and status

### Application Metrics
- `app_users_total`: Total number of users
- `db_connections`: Current database connections
- `cache_hits_total`: Total cache hits
- `cache_misses_total`: Total cache misses

## Alerting

The monitoring setup includes alerting for:
- High error rates (>10 errors/minute)
- Slow response times (>2s P95)
- Service downtime

## Security Considerations

- Restrict access to monitoring endpoints in production
- Use authentication for Prometheus and Grafana
- Monitor for unauthorized access to metrics endpoints
- Use HTTPS for all monitoring traffic

## Scaling Considerations

- Prometheus storage scales with retention time and metric cardinality
- Consider remote storage for long-term metrics
- Use federation for multi-cluster setups
- Scale Grafana with multiple instances behind a load balancer

## Troubleshooting

### Common Issues

**1. Metrics Not Appearing**
- Verify the `/metrics` endpoint is accessible
- Check Prometheus configuration for correct target
- Ensure prometheus-client is installed in the backend

**2. High Memory Usage**
- Reduce metric retention time
- Limit metric cardinality
- Use Prometheus TSDB compaction

**3. Slow Queries in Grafana**
- Optimize PromQL queries
- Add appropriate indexes
- Use recording rules for expensive calculations

## Best Practices

- Monitor business metrics, not just technical metrics
- Set up alerts for SLA violations
- Use recording rules to pre-calculate expensive queries
- Regularly review and clean up unused dashboards
- Implement log aggregation alongside metrics

## Integration with Existing System

The Prometheus metrics are automatically integrated with the existing metrics system in the application. The new `prometheus_metrics.py` middleware captures the same metrics that were previously collected but now exports them in Prometheus format.

---
**Document Version**: 1.0  
**Last Updated**: January 2026