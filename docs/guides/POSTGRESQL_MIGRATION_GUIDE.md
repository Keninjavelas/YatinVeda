# Database Migration Guide - SQLite to PostgreSQL

## Overview

This guide explains how to migrate the YatinVeda application from SQLite (development) to PostgreSQL (production) for improved scalability, concurrency, and reliability.

## Why PostgreSQL for Production?

- **Concurrency**: Better handling of multiple concurrent connections
- **Performance**: Superior performance under load compared to SQLite
- **Reliability**: ACID-compliant with better crash recovery
- **Scalability**: Horizontal scaling capabilities
- **Features**: Advanced indexing, JSON support, full-text search

## Prerequisites

- PostgreSQL server installed and running
- Application server with network access to PostgreSQL
- Updated application configuration

## Migration Steps

### 1. Install PostgreSQL Dependencies

Update `backend/requirements.txt` or `backend/pyproject.toml`:

```toml
# Add PostgreSQL driver to pyproject.toml
[tool.poetry.dependencies]
psycopg2-binary = "^2.9.0"  # or asyncpg for async operations
SQLAlchemy = "^2.0.0"
```

Or in requirements.txt:
```
psycopg2-binary>=2.9.0
SQLAlchemy>=2.0.0
```

### 2. Database Configuration

The application now uses the `database_config.py` module which automatically detects the database type and applies appropriate configuration.

### 3. Environment Configuration

Create a production environment file `.env.production`:

```env
# Production Database Configuration
DATABASE_URL=postgresql://username:password@hostname:5432/yatinveda_db
ENVIRONMENT=production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Security Settings
COOKIE_SECURE=true
REFRESH_TOKEN_BINDING=true
SECRET_KEY=your-production-secret-key

# Other Production Settings
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

### 4. Docker Configuration

Update `docker-compose.yml` for PostgreSQL:

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
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
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
```

### 5. Database Migration Commands

Run Alembic migrations against PostgreSQL:

```bash
# Set environment to production
export DATABASE_URL="postgresql://username:password@localhost:5432/yatinveda_db"
export ENVIRONMENT=production

# Run migrations
cd backend
alembic upgrade head
```

### 6. Data Migration (if needed)

If migrating from existing SQLite data, use a data transfer script:

```python
# migrate_data.py
import sqlite3
import psycopg2
from sqlalchemy import create_engine, text
import json

def migrate_sqlite_to_postgresql(sqlite_path, postgres_url):
    """Migrate data from SQLite to PostgreSQL."""
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_engine = create_engine(postgres_url)
    
    # Get table names from SQLite
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    for table in tables:
        if table.startswith('alembic_'):  # Skip alembic tables
            continue
            
        # Get all data from SQLite table
        sqlite_cursor.execute(f"SELECT * FROM {table};")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            continue
            
        # Get column names
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Insert into PostgreSQL
        with pg_engine.connect() as conn:
            # Build INSERT statement
            placeholders = ', '.join([':' + col for col in columns])
            insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Prepare data for insertion
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Handle JSON columns (convert string to dict for PostgreSQL)
                for col_name, value in row_dict.items():
                    if isinstance(value, str):
                        try:
                            # Try to parse as JSON
                            parsed = json.loads(value)
                            row_dict[col_name] = parsed
                        except (json.JSONDecodeError, TypeError):
                            # Not JSON, keep as string
                            pass
                
                conn.execute(text(insert_sql), row_dict)
            
            conn.commit()
    
    sqlite_conn.close()

# Usage
if __name__ == "__main__":
    migrate_sqlite_to_postgresql(
        "yatinveda.db",
        "postgresql://username:password@localhost:5432/yatinveda_db"
    )
```

### 7. Connection Pooling Configuration

The `database_config.py` module includes production-ready connection pooling:

- **Pool Size**: Number of connections to maintain in the pool
- **Max Overflow**: Maximum number of connections beyond pool size
- **Pool Timeout**: Seconds to wait for connection before giving up
- **Pool Recycle**: Seconds after which connections are recycled

### 8. Health Checks

Add database health check endpoint to your application:

```python
@app.get("/health/database")
async def database_health_check():
    """Health check for database connectivity."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row:
                return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

### 9. Monitoring and Logging

Enable database query logging in production:

```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 10. Performance Optimization

PostgreSQL-specific optimizations:

- **Indexing**: Create indexes on frequently queried columns
- **Connection Pooling**: Use PgBouncer for connection pooling at scale
- **Partitioning**: Partition large tables if needed
- **Vacuum**: Regular maintenance with autovacuum

## Testing the Migration

### 1. Connection Test

```bash
# Test database connection
python -c "from database_config import test_connection; print(test_connection())"
```

### 2. Application Test

Start the application with PostgreSQL configuration:

```bash
# Copy production env file
cp .env.production .env

# Start with Docker
docker-compose up -d

# Test API endpoints
curl -X GET http://localhost:8000/health
```

### 3. Load Test

```bash
# Simple load test to verify concurrency
ab -n 1000 -c 10 http://localhost:8000/health
```

## Rollback Plan

In case of issues:

1. Stop the application
2. Restore from database backup if needed
3. Revert to SQLite configuration temporarily
4. Investigate and fix issues
5. Retry PostgreSQL migration

## Security Considerations

- **Network Security**: Use SSL connections to PostgreSQL
- **Credentials**: Store credentials securely, use environment variables
- **Permissions**: Grant minimal required permissions to database user
- **Auditing**: Enable PostgreSQL logging for security monitoring

## Scaling Considerations

- **Read Replicas**: Add read replicas for read-heavy workloads
- **Sharding**: Consider sharding for very large datasets
- **Caching**: Implement Redis for frequently accessed data
- **Monitoring**: Set up alerts for database performance metrics

## Troubleshooting

### Common Issues

**1. Connection Issues**
- Verify PostgreSQL is running and accessible
- Check credentials and host/port settings
- Ensure firewall allows connections

**2. Permission Issues**
- Verify database user has required permissions
- Check that the database exists

**3. Performance Issues**
- Review connection pool settings
- Check for missing indexes
- Monitor query performance

### Diagnostic Commands

```bash
# Check PostgreSQL status
pg_isready -h hostname -p 5432 -U username

# View active connections
psql -h hostname -U username -d yatinveda_db -c "SELECT * FROM pg_stat_activity;"

# Check database size
psql -h hostname -U username -d yatinveda_db -c "SELECT pg_size_pretty(pg_database_size('yatinveda_db'));"
```

## Conclusion

The migration to PostgreSQL provides significant benefits for production deployment of YatinVeda:

- Improved performance under load
- Better concurrency handling
- Enhanced reliability and data integrity
- Scalability for future growth
- Enterprise-grade features

Follow this guide carefully to ensure a smooth transition from SQLite to PostgreSQL while maintaining application functionality and data integrity.

---
**Document Version**: 1.0  
**Last Updated**: January 2026