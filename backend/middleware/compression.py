"""Response compression middleware for reducing bandwidth and improving performance.

Supports gzip and brotli compression with intelligent content-type detection.
Only compresses responses above a minimum size threshold.
"""

import gzip
import logging
from typing import Callable, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger.warning("Brotli not available. Install with: pip install brotli")


class CompressionMiddleware(BaseHTTPMiddleware):
    """Compress HTTP responses using gzip or brotli.
    
    Features:
    - Automatic compression format selection based on Accept-Encoding
    - Configurable minimum response size threshold
    - Content-type filtering (only compress compressible types)
    - Preserves response headers
    - Adds compression metadata headers
    """
    
    # Content types that benefit from compression
    COMPRESSIBLE_TYPES: Set[str] = {
        "text/html",
        "text/css",
        "text/plain",
        "text/xml",
        "text/javascript",
        "application/javascript",
        "application/x-javascript",
        "application/json",
        "application/xml",
        "application/rss+xml",
        "application/atom+xml",
        "application/xhtml+xml",
        "application/ld+json",
        "image/svg+xml",
        # Image formats that can be compressed
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "image/bmp",
    }
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,
        compression_level: int = 6,
        brotli_quality: int = 4,
    ):
        """Initialize compression middleware.
        
        Args:
            app: ASGI application
            minimum_size: Minimum response size in bytes to compress (default: 500)
            compression_level: Gzip compression level 0-9 (default: 6)
            brotli_quality: Brotli quality level 0-11 (default: 4)
        """
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.brotli_quality = brotli_quality
    
    def should_compress(self, response: Response) -> bool:
        """Determine if response should be compressed.
        
        Args:
            response: Response object
            
        Returns:
            True if response should be compressed
        """
        # Check if already compressed
        if "content-encoding" in response.headers:
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in self.COMPRESSIBLE_TYPES:
            return False
        
        # Check if response has a body
        if not hasattr(response, "body") or not response.body:
            return False
        
        # Check minimum size
        content_length = len(response.body)
        if content_length < self.minimum_size:
            return False
        
        return True
    
    def get_compression_method(self, accept_encoding: str) -> str:
        """Determine best compression method from Accept-Encoding header.
        
        Args:
            accept_encoding: Accept-Encoding header value
            
        Returns:
            Compression method: 'br', 'gzip', or 'none'
        """
        if not accept_encoding:
            return "none"
        
        accept_encoding = accept_encoding.lower()
        
        # Prefer brotli if available and supported by client
        if BROTLI_AVAILABLE and "br" in accept_encoding:
            return "br"
        
        # Fall back to gzip
        if "gzip" in accept_encoding:
            return "gzip"
        
        return "none"
    
    def compress_gzip(self, content: bytes) -> bytes:
        """Compress content using gzip.
        
        Args:
            content: Content to compress
            
        Returns:
            Compressed content
        """
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=self.compression_level) as gz:
            gz.write(content)
        return buffer.getvalue()
    
    def compress_brotli(self, content: bytes) -> bytes:
        """Compress content using brotli.
        
        Args:
            content: Content to compress
            
        Returns:
            Compressed content
        """
        if not BROTLI_AVAILABLE:
            raise RuntimeError("Brotli not available")
        return brotli.compress(content, quality=self.brotli_quality)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and compress response if appropriate."""
        # Get response from next middleware/handler
        response: Response = await call_next(request)
        
        # Skip compression for streaming responses
        if isinstance(response, StreamingResponse):
            return response
        
        # Check if compression is appropriate
        if not self.should_compress(response):
            return response
        
        # Get client's accepted encodings
        accept_encoding = request.headers.get("accept-encoding", "")
        compression_method = self.get_compression_method(accept_encoding)
        
        if compression_method == "none":
            return response
        
        # Compress response body
        original_size = len(response.body)
        
        try:
            if compression_method == "br":
                compressed_body = self.compress_brotli(response.body)
                encoding = "br"
            else:  # gzip
                compressed_body = self.compress_gzip(response.body)
                encoding = "gzip"
            
            compressed_size = len(compressed_body)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            # Only use compressed version if it's actually smaller
            if compressed_size < original_size:
                # Update response
                response.body = compressed_body
                response.headers["content-encoding"] = encoding
                response.headers["content-length"] = str(compressed_size)
                
                # Add compression metadata for monitoring
                response.headers["x-compression-ratio"] = f"{compression_ratio:.1f}%"
                response.headers["x-original-size"] = str(original_size)
                
                logger.debug(
                    f"Compressed response: {original_size} -> {compressed_size} bytes "
                    f"({compression_ratio:.1f}% reduction) using {encoding}"
                )
            
        except Exception as e:
            logger.error(f"Compression failed: {e}", exc_info=True)
            # Return uncompressed response on error
        
        # Ensure Vary header includes Accept-Encoding
        vary = response.headers.get("vary", "")
        if "accept-encoding" not in vary.lower():
            response.headers["vary"] = f"{vary}, Accept-Encoding".strip(", ")
        
        return response


__all__ = ["CompressionMiddleware", "BROTLI_AVAILABLE"]
