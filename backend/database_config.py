"""
Production Database Configuration for YatinVeda

This module handles environment-specific database configuration with support for
SQLite (development) and PostgreSQL (production) with connection pooling,
connection timeouts, and security best practices.
"""

import os
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging


logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration manager for different environments."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./yatinveda.db")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment."""
        return self.database_url
    
    def is_postgresql(self) -> bool:
        """Check if the database URL is for PostgreSQL."""
        return self.database_url.lower().startswith('postgresql')
    
    def is_sqlite(self) -> bool:
        """Check if the database URL is for SQLite."""
        return self.database_url.lower().startswith('sqlite')
    
    def get_engine_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration based on database type."""
        base_config = {
            "poolclass": QueuePool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo,
            "pool_pre_ping": True,  # Verify connections before use
        }
        
        if self.is_sqlite():
            # SQLite-specific configuration
            base_config.update({
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,  # 30 second timeout for SQLite locks
                }
            })
        elif self.is_postgresql():
            # PostgreSQL-specific configuration
            base_config.update({
                "connect_args": {
                    "connect_timeout": 10,
                    "application_name": "yatinveda_backend",
                },
                "pool_pre_ping": True,
                "pool_recycle": self.pool_recycle,
            })
        else:
            # Default configuration for other databases
            base_config.update({
                "pool_pre_ping": True,
            })
        
        return base_config
    
    def create_engine(self):
        """Create SQLAlchemy engine with appropriate configuration."""
        engine_config = self.get_engine_config()
        database_url = self.get_database_url()
        
        logger.info(f"Creating database engine for: {database_url.split('://')[0]}")
        logger.info(f"Environment: {self.environment}")
        
        if self.is_postgresql():
            # Validate PostgreSQL URL format
            parsed = urlparse(database_url)
            if not all([parsed.scheme, parsed.hostname, parsed.path]):
                raise ValueError(f"Invalid PostgreSQL URL format: {database_url}")
        
        return create_engine(database_url, **engine_config)
    
    def get_sessionmaker(self, engine):
        """Get configured sessionmaker."""
        return sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )


# Global configuration instance
db_config = DatabaseConfig()

# Create engine and sessionmaker instances
engine = db_config.create_engine()
SessionLocal = db_config.get_sessionmaker(engine)


def init_db() -> None:
    """Initialize database schema for the configured engine."""
    from models.database import Base
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync():
    """Synchronous database session for background tasks."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connection."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row:
                logger.info("Database connection test successful")
                return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False


# Environment-specific validation
def validate_environment():
    """Validate database configuration for the current environment."""
    if db_config.environment == "production":
        if db_config.is_sqlite():
            logger.warning("WARNING: SQLite is not recommended for production!")
            logger.warning("Consider migrating to PostgreSQL for production use.")
        
        required_vars = ["DATABASE_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"Missing environment variables for production: {missing_vars}")
    
    if db_config.is_postgresql():
        # Additional PostgreSQL validation
        parsed = urlparse(db_config.database_url)
        if parsed.password and '@' in parsed.password:
            logger.warning("WARNING: Database password may contain special characters that need URL encoding!")


# Run validation on import
validate_environment()