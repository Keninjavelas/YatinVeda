# Synthetic Monitoring

Synthetic monitoring validates that YatinVeda's critical user flows are functioning correctly by making real HTTP requests on a schedule — independent of internal Prometheus metrics.

## Endpoints to Monitor

| Endpoint | Method | Expected | Interval | Severity |
|----------|--------|----------|----------|----------|
| `/` | GET | 200 + JSON `status: "active"` | 1 min | Critical |
| `/api/v1/health` | GET | 200 + JSON `status: "healthy"` | 1 min | Critical |
| `/api/v1/readiness` | GET | 200 + JSON `ready: true` | 2 min | Critical |
| Front-end (root) | GET | 200 + HTML contains `YatinVeda` | 2 min | High |
| `/docs` | GET | 200 (Swagger UI) | 5 min | Low |

## Option A — External SaaS (recommended for production)

Use any uptime monitoring service. Example configuration for **UptimeRobot** (free tier supports 50 monitors):

1. Sign up at https://uptimerobot.com
2. Create monitors for each endpoint above
3. Set alert contacts (email, Slack webhook, PagerDuty)
4. Configure status page at `status.yatinveda.com`

### UptimeRobot keyword monitors

| Monitor Name | URL | Type | Keyword |
|---|---|---|---|
| API Root | `https://api.yatinveda.com/` | Keyword | `active` |
| Health Check | `https://api.yatinveda.com/api/v1/health` | Keyword | `healthy` |
| Readiness | `https://api.yatinveda.com/api/v1/readiness` | Keyword | `true` |
| Frontend | `https://yatinveda.com/` | Keyword | `YatinVeda` |

## Option B — Self-hosted with Prometheus Blackbox Exporter

Add the blackbox exporter to your Docker Compose or Kubernetes deployment for internal synthetic probes.

### Docker Compose snippet

```yaml
# Add to docker-compose.yml
blackbox-exporter:
  image: prom/blackbox-exporter:latest
  volumes:
    - ./monitoring/blackbox.yml:/config/blackbox.yml:ro
  command: --config.file=/config/blackbox.yml
  ports:
    - "9115:9115"
  networks:
    - yatinveda-network
```

### Blackbox config (`monitoring/blackbox.yml`)

Already generated — see `monitoring/blackbox.yml`.

### Prometheus scrape config addition

```yaml
# Add to monitoring/prometheus.yml → scrape_configs
- job_name: "blackbox-http"
  metrics_path: /probe
  params:
    module: [http_2xx]
  static_configs:
    - targets:
        - http://backend:8000/
        - http://backend:8000/api/v1/health
        - http://backend:8000/api/v1/readiness
        - http://frontend:3000/
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: blackbox-exporter:9115

- job_name: "blackbox-health-body"
  metrics_path: /probe
  params:
    module: [http_health_body]
  static_configs:
    - targets:
        - http://backend:8000/api/v1/health
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: blackbox-exporter:9115
```

### Prometheus alert rules for synthetic probes

```yaml
# Add to monitoring/alerts.yml
- name: yatinveda-synthetic
  rules:
    - alert: EndpointDown
      expr: probe_success == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Endpoint {{ $labels.instance }} is down"
        description: "Blackbox probe has failed for {{ $labels.instance }} for 2+ minutes."

    - alert: SlowEndpoint
      expr: probe_duration_seconds > 5
      for: 3m
      labels:
        severity: warning
      annotations:
        summary: "Endpoint {{ $labels.instance }} is slow ({{ $value }}s)"
        description: "Probe latency exceeds 5 seconds for 3+ minutes."

    - alert: SSLCertExpiringSoon
      expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 14
      for: 1h
      labels:
        severity: warning
      annotations:
        summary: "SSL certificate for {{ $labels.instance }} expires in < 14 days"
```

## Option C — Lightweight cron script

For simple setups, use `monitoring/synthetic_probe.sh` (generated alongside this doc) as a cron job:

```cron
# Run every 2 minutes
*/2 * * * * /opt/yatinveda/monitoring/synthetic_probe.sh >> /var/log/yatinveda-probe.log 2>&1
```

## Grafana Dashboard

Import the blackbox exporter community dashboard (ID **7587**) into Grafana for visualizing probe results alongside application metrics.
