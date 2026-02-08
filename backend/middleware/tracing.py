"""OpenTelemetry distributed tracing for observability.

Provides automatic instrumentation and trace context propagation
for better visibility into request flows and performance.
"""

from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry packages
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat
    
    # Try to import OTLP exporter for production
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        OTLP_AVAILABLE = True
    except ImportError:
        OTLP_AVAILABLE = False
    
    # Try to import Jaeger exporter as alternative
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        JAEGER_AVAILABLE = True
    except ImportError:
        JAEGER_AVAILABLE = False
    
    OTEL_AVAILABLE = True
    
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry packages not installed. Tracing disabled.")


class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    
    def __init__(
        self,
        service_name: str = "yatinveda-backend",
        environment: str = "development",
        otlp_endpoint: Optional[str] = None,
        jaeger_endpoint: Optional[str] = None,
        sample_rate: float = 1.0,
        console_export: bool = False,
    ):
        """Initialize tracing configuration.
        
        Args:
            service_name: Name of the service
            environment: Deployment environment
            otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
            jaeger_endpoint: Jaeger agent endpoint (e.g., "localhost:6831")
            sample_rate: Sampling rate (0.0 to 1.0)
            console_export: Export traces to console for debugging
        """
        self.service_name = service_name
        self.environment = environment
        self.otlp_endpoint = otlp_endpoint
        self.jaeger_endpoint = jaeger_endpoint
        self.sample_rate = sample_rate
        self.console_export = console_export


_tracing_enabled = False
_tracer: Optional[Any] = None


def setup_tracing(config: Optional[TracingConfig] = None) -> bool:
    """Set up OpenTelemetry tracing.
    
    Args:
        config: Tracing configuration (uses defaults if None)
        
    Returns:
        True if tracing was set up successfully
    """
    global _tracing_enabled, _tracer
    
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available. Install with: pip install opentelemetry-distro opentelemetry-exporter-otlp")
        return False
    
    # Use default config if not provided
    if config is None:
        config = TracingConfig(
            service_name=os.getenv("SERVICE_NAME", "yatinveda-backend"),
            environment=os.getenv("ENVIRONMENT", "development"),
            otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
            jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
            console_export=os.getenv("TRACE_CONSOLE_EXPORT", "false").lower() == "true",
        )
    
    try:
        # Create resource with service information
        resource = Resource(attributes={
            SERVICE_NAME: config.service_name,
            "environment": config.environment,
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add exporters
        exporters_added = False
        
        # OTLP exporter (preferred for production)
        if config.otlp_endpoint and OTLP_AVAILABLE:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                exporters_added = True
                logger.info(f"OTLP trace exporter configured: {config.otlp_endpoint}")
            except Exception as e:
                logger.error(f"Failed to configure OTLP exporter: {e}")
        
        # Jaeger exporter (alternative)
        elif config.jaeger_endpoint and JAEGER_AVAILABLE:
            try:
                agent_host, agent_port = config.jaeger_endpoint.split(":")
                jaeger_exporter = JaegerExporter(
                    agent_host_name=agent_host,
                    agent_port=int(agent_port),
                )
                provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
                exporters_added = True
                logger.info(f"Jaeger trace exporter configured: {config.jaeger_endpoint}")
            except Exception as e:
                logger.error(f"Failed to configure Jaeger exporter: {e}")
        
        # Console exporter (for debugging)
        if config.console_export:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            exporters_added = True
            logger.info("Console trace exporter configured")
        
        if not exporters_added:
            logger.warning("No trace exporters configured. Traces will not be sent anywhere.")
            # Still enable tracing for context propagation
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Set up context propagation (B3 format for compatibility)
        set_global_textmap(B3MultiFormat())
        
        # Get tracer instance
        _tracer = trace.get_tracer(__name__)
        _tracing_enabled = True
        
        logger.info(f"Tracing enabled for service: {config.service_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up tracing: {e}", exc_info=True)
        return False


def instrument_app(app) -> bool:
    """Instrument FastAPI application with automatic tracing.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        True if instrumentation was successful
    """
    if not OTEL_AVAILABLE:
        return False
    
    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")
        return True
        
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")
        return False


def instrument_sqlalchemy(engine) -> bool:
    """Instrument SQLAlchemy engine with automatic tracing.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        True if instrumentation was successful
    """
    if not OTEL_AVAILABLE:
        return False
    
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy instrumented for tracing")
        return True
        
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}")
        return False


def instrument_redis() -> bool:
    """Instrument Redis client with automatic tracing.
    
    Returns:
        True if instrumentation was successful
    """
    if not OTEL_AVAILABLE:
        return False
    
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented for tracing")
        return True
        
    except Exception as e:
        logger.error(f"Failed to instrument Redis: {e}")
        return False


def get_tracer():
    """Get the global tracer instance.
    
    Returns:
        Tracer instance or None if tracing is disabled
    """
    return _tracer


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled.
    
    Returns:
        True if tracing is enabled
    """
    return _tracing_enabled


def create_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Create a new span for manual instrumentation.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        
    Returns:
        Span context manager or no-op context if tracing disabled
        
    Usage:
        with create_span("expensive_operation", {"user_id": 123}):
            # Your code here
            result = expensive_function()
    """
    if not _tracing_enabled or _tracer is None:
        # Return no-op context manager
        from contextlib import nullcontext
        return nullcontext()
    
    span = _tracer.start_as_current_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span


def add_span_attribute(key: str, value: Any) -> None:
    """Add attribute to current span.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    if not _tracing_enabled:
        return
    
    try:
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, value)
    except Exception as e:
        logger.debug(f"Failed to add span attribute: {e}")


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add event to current span.
    
    Args:
        name: Event name
        attributes: Optional event attributes
    """
    if not _tracing_enabled:
        return
    
    try:
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes=attributes or {})
    except Exception as e:
        logger.debug(f"Failed to add span event: {e}")


def record_exception(exception: Exception) -> None:
    """Record exception in current span.
    
    Args:
        exception: Exception to record
    """
    if not _tracing_enabled:
        return
    
    try:
        current_span = trace.get_current_span()
        if current_span:
            current_span.record_exception(exception)
    except Exception as e:
        logger.debug(f"Failed to record exception: {e}")


__all__ = [
    "TracingConfig",
    "setup_tracing",
    "instrument_app",
    "instrument_sqlalchemy",
    "instrument_redis",
    "get_tracer",
    "is_tracing_enabled",
    "create_span",
    "add_span_attribute",
    "add_span_event",
    "record_exception",
]
