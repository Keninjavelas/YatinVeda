# Redis Cache & OpenTelemetry Setup Guide

## Overview

This guide explains how to set up optional advanced features for production deployments:
- **Redis Cache**: Distributed caching for scalability
- **OpenTelemetry Tracing**: Distributed tracing for observability

Both features are optional and the application works without them.

---

## Redis Cache Setup

### Why Redis?

- **Distributed Caching**: Share cache across multiple instances
- **Persistence**: Cache survives application restarts
- **Performance**: Faster than in-memory for large datasets
- **Production-Ready**: Used by companies like GitHub, Twitter, Stack Overflow

### Installation

#### Option 1: Docker (Recommended for Development)

```bash
# Run Redis in Docker
docker run -d \
  --name yatinveda-redis \
  -p 6379:6379 \
  redis:7-alpine

# With persistence
docker run -d \
  --name yatinveda-redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes
```

#### Option 2: Local Installation

**Windows** (using Chocolatey):
```powershell
choco install redis-64
redis-server
```

**macOS** (using Homebrew):
```bash
brew install redis
brew services start redis
```

**Linux** (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### Option 3: Cloud Managed Redis

- **AWS ElastiCache**: Fully managed Redis
- **Azure Cache for Redis**: Azure-hosted Redis
- **Redis Cloud**: Official Redis cloud service
- **Google Cloud Memorystore**: Google Cloud Redis

### Configuration

1. **Install Python Package**:
```bash
pip install redis==5.0.1
```

2. **Set Environment Variables** (in `.env`):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional, leave empty if no password
```

3. **Test Connection**:
```bash
# Using redis-cli
redis-cli ping
# Should return: PONG

# Using Python
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
```

### Usage in Application

The application automatically detects and uses Redis if available:

```python
from middleware import get_redis_cache

# Get cache instance
cache = get_redis_cache()

# Basic operations
cache.set("key", {"data": "value"}, ttl=300)
value = cache.get("key")

# Using decorator
from middleware import redis_cached

@redis_cached(ttl=600, key_prefix="users")
def get_user_profile(user_id: int):
    # Expensive database query
    return db.query(User).filter(User.id == user_id).first()
```

### Fallback Behavior

If Redis is unavailable:
- Application automatically falls back to in-memory cache
- No errors or crashes
- Warning logged: "Redis unavailable, using in-memory fallback"
- Application continues to work normally

### Monitoring Redis

```bash
# Redis CLI monitor (real-time commands)
redis-cli monitor

# Get info
redis-cli info

# Check memory usage
redis-cli info memory

# List all keys
redis-cli keys '*'

# Get cache statistics via API
curl http://localhost:8000/api/v1/metrics | jq '.cache_metrics'
```

---

## OpenTelemetry Tracing Setup

### Why OpenTelemetry?

- **Distributed Tracing**: Track requests across multiple services
- **Performance Analysis**: Identify slow database queries, API calls
- **Debugging**: Understand request flow and dependencies
- **Standards-Based**: Works with Jaeger, Zipkin, Cloud providers

### Architecture

```
Your App → OpenTelemetry SDK → Exporter → Backend
                                          ├─ Jaeger (open source)
                                          ├─ Zipkin (open source)
                                          ├─ OTLP Collector
                                          ├─ AWS X-Ray
                                          ├─ Azure Monitor
                                          └─ Google Cloud Trace
```

### Installation

#### 1. Install Python Packages

```bash
pip install \
  opentelemetry-api==1.21.0 \
  opentelemetry-sdk==1.21.0 \
  opentelemetry-instrumentation-fastapi==0.42b0 \
  opentelemetry-instrumentation-sqlalchemy==0.42b0 \
  opentelemetry-instrumentation-redis==0.42b0 \
  opentelemetry-exporter-otlp==1.21.0 \
  opentelemetry-exporter-jaeger==1.21.0
```

#### 2. Set Up Tracing Backend

**Option A: Jaeger (Recommended for Development)**

```bash
# Run Jaeger all-in-one (Docker)
docker run -d \
  --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# Access Jaeger UI
# Open browser: http://localhost:16686
```

**Option B: OTLP Collector**

```bash
# Download OpenTelemetry Collector
# See: https://opentelemetry.io/docs/collector/getting-started/

# Run collector
docker run -d \
  --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  otel/opentelemetry-collector:latest
```

**Option C: Cloud Providers**

- **AWS X-Ray**: Set `OTLP_ENDPOINT` to X-Ray daemon
- **Azure Monitor**: Use Application Insights exporter
- **Google Cloud**: Set `OTLP_ENDPOINT` to Cloud Trace

### Configuration

**Set Environment Variables** (in `.env`):

```bash
# Service identification
SERVICE_NAME=yatinveda-backend
ENVIRONMENT=production

# For Jaeger
JAEGER_ENDPOINT=localhost:6831

# OR for OTLP Collector
OTLP_ENDPOINT=http://localhost:4317

# For debugging (console export)
TRACE_CONSOLE_EXPORT=false
```

### Application Integration

Tracing is automatically configured if packages are installed:

```python
# In main.py (already integrated)
from middleware import setup_tracing, instrument_app, instrument_sqlalchemy

# Set up tracing
setup_tracing()

# Instrument FastAPI
instrument_app(app)

# Instrument SQLAlchemy
from database import engine
instrument_sqlalchemy(engine)
```

### Manual Instrumentation

For custom spans:

```python
from middleware import create_span, add_span_attribute

# Create custom span
with create_span("expensive_calculation", {"user_id": user_id}):
    result = perform_calculation()
    add_span_attribute("result_size", len(result))
```

### Viewing Traces

#### Jaeger UI

1. Open http://localhost:16686
2. Select service: "yatinveda-backend"
3. Click "Find Traces"
4. View trace details, timing, dependencies

**Example Trace Flow**:
```
HTTP GET /api/v1/prescriptions
  ├─ Database Query: SELECT * FROM prescriptions
  ├─ Cache Check: Redis GET prescription:123
  ├─ PDF Generation
  └─ Response Compression
```

### Trace Attributes

Automatic instrumentation adds:
- **HTTP**: Method, URL, status code, user agent
- **Database**: Query, duration, connection info
- **Redis**: Command, key, duration
- **Custom**: Your business logic attributes

### Performance Impact

- **Negligible**: < 1% overhead in most cases
- **Sampling**: Can configure sampling rate (e.g., 10% of requests)
- **Async**: Traces sent asynchronously, no blocking

### Troubleshooting

**Traces not appearing?**

```bash
# Check if packages are installed
python -c "from opentelemetry import trace; print('OK')"

# Verify backend is running
# Jaeger: curl http://localhost:16686
# OTLP: curl http://localhost:4317

# Enable console export for debugging
TRACE_CONSOLE_EXPORT=true python main.py
```

**Connection errors?**

```bash
# Check environment variables
echo $JAEGER_ENDPOINT
echo $OTLP_ENDPOINT

# Verify network connectivity
nc -zv localhost 6831  # Jaeger
nc -zv localhost 4317  # OTLP
```

---

## Production Deployment

### Docker Compose Example

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - REDIS_HOST=redis
      - JAEGER_ENDPOINT=jaeger:6831
    depends_on:
      - redis
      - jaeger
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
  
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Agent

volumes:
  redis-data:
```

### Kubernetes Example

See `kubernetes-deployment-example.yaml` for complete configuration.

**Redis**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        args: ["redis-server", "--appendonly", "yes"]
        volumeMounts:
        - name: redis-data
          mountPath: /data
```

**Environment Variables**:
```yaml
env:
- name: REDIS_HOST
  value: "redis"
- name: REDIS_PORT
  value: "6379"
- name: JAEGER_ENDPOINT
  value: "jaeger-agent:6831"
```

---

## Cost Considerations

### Redis

**Self-Hosted**:
- Free (open source)
- Hardware/VM costs only

**Managed Services**:
- AWS ElastiCache: ~$15-50/month (small instances)
- Azure Cache: ~$20-60/month
- Redis Cloud: Free tier available, ~$7/month for 30MB

### OpenTelemetry

**Self-Hosted** (Jaeger/Zipkin):
- Free (open source)
- Storage costs only

**Managed Services**:
- AWS X-Ray: $5 per 1M traces
- Azure Application Insights: Included with App Service
- Google Cloud Trace: Free tier (5M spans/month)

---

## Best Practices

### Redis

✅ **DO**:
- Use Redis in production for multi-instance deployments
- Configure persistence (AOF or RDB)
- Set up replication for high availability
- Monitor memory usage
- Use appropriate TTL values

❌ **DON'T**:
- Store sensitive data without encryption
- Use Redis as primary database
- Forget to configure max memory limits
- Ignore eviction policies

### OpenTelemetry

✅ **DO**:
- Start with sampling in high-traffic apps (10-20%)
- Use attribute naming conventions
- Add business context to spans
- Monitor collector health
- Set up alerts on trace errors

❌ **DON'T**:
- Log sensitive data in span attributes
- Create too many custom spans (overhead)
- Forget to handle exporter failures
- Ignore high cardinality attributes

---

## Monitoring & Alerting

### Health Checks

Both features are monitored via health endpoints:

```bash
# Check cache health
curl http://localhost:8000/api/v1/health | jq '.checks.cache'

# Response:
{
  "status": "healthy",
  "backend": "redis",
  "redis_available": true
}
```

### Metrics

```bash
# Cache metrics
curl http://localhost:8000/api/v1/metrics | jq '.cache_metrics'

# Response:
{
  "hits": 1250,
  "misses": 150,
  "hit_rate": "89.29%",
  "redis_available": true,
  "redis_used_memory_human": "2.5M"
}
```

### Alerts

Set up alerts for:
- Redis connection failures
- Low cache hit rate (< 70%)
- High trace error rate
- Slow trace percentiles (p99 > 1s)

---

## Summary

| Feature | Status | Required | Installation |
|---------|--------|----------|--------------|
| **In-Memory Cache** | ✅ Active | Yes | Built-in |
| **Redis Cache** | 🔧 Optional | No | `pip install redis` |
| **OpenTelemetry** | 🔧 Optional | No | `pip install opentelemetry-*` |

Both features enhance production deployments but are **not required** for the application to function. The app gracefully falls back to simpler alternatives if these services are unavailable.

---

## Quick Start

### Enable Redis

```bash
# 1. Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# 2. Install package
pip install redis==5.0.1

# 3. Set environment variable
echo "REDIS_HOST=localhost" >> .env

# 4. Restart application
python main.py

# 5. Verify
curl http://localhost:8000/api/v1/health | jq '.checks.cache.backend'
# Should return: "redis"
```

### Enable Tracing

```bash
# 1. Start Jaeger
docker run -d -p 6831:6831/udp -p 16686:16686 jaegertracing/all-in-one

# 2. Install packages
pip install opentelemetry-api opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-exporter-jaeger

# 3. Set environment variables
echo "SERVICE_NAME=yatinveda-backend" >> .env
echo "JAEGER_ENDPOINT=localhost:6831" >> .env

# 4. Restart application
python main.py

# 5. View traces
# Open browser: http://localhost:16686
```

---

For questions or issues, see the main documentation or create an issue in the repository.
