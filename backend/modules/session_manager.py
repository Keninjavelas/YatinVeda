"""
Redis-based session management for YatinVeda backend.

Provides distributed session storage with Redis for scalability across multiple instances.
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import logging
import os

# Redis imports (optional dependency)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information stored about a user session."""
    session_id: str
    user_id: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class RedisSessionManager:
    """Redis-based session manager for distributed session storage.
    
    For production deployments with multiple instances.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        session_ttl: int = 86400  # 24 hours in seconds
    ):
        """Initialize Redis session manager.
        
        Args:
            redis_url: Redis connection URL
            session_ttl: Session time-to-live in seconds (default: 24 hours)
        """
        self.redis_url = redis_url
        self.session_ttl = session_ttl
        self.redis_client = None
        self.key_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis is not available. Session management will be disabled.")
    
    async def _get_redis(self):
        """Get Redis client, creating if necessary"""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install with: pip install redis")
        
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client
    
    async def create_session(
        self, 
        user_id: int, 
        user_agent: Optional[str] = None, 
        ip_address: Optional[str] = None,
        device_name: Optional[str] = None
    ):  # -> SessionInfo:
        """Create a new session for a user.
        
        Args:
            user_id: User ID
            user_agent: User agent string
            ip_address: IP address
            device_name: Device name (optional)
            
        Returns:
            SessionInfo object with session details
        """
        if not REDIS_AVAILABLE:
            return None
            
        try:
            client = await self._get_redis()
            
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Create session info
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.session_ttl)
            
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                user_agent=user_agent,
                ip_address=ip_address,
                device_name=device_name,
                created_at=now,
                last_accessed=now,
                expires_at=expires_at
            )
            
            # Store session in Redis
            session_key = f"{self.key_prefix}{session_id}"
            session_data = {
                "user_id": user_id,
                "user_agent": user_agent or "",
                "ip_address": ip_address or "",
                "device_name": device_name or "",
                "created_at": now.isoformat(),
                "last_accessed": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "is_active": True
            }
            
            await client.hset(session_key, mapping=session_data)
            await client.expire(session_key, self.session_ttl)
            
            # Add session to user's session list
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            await client.sadd(user_sessions_key, session_id)
            await client.expire(user_sessions_key, self.session_ttl)
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_info
            
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {str(e)}")
            return None
    
    async def get_session(self, session_id: str):
        # Return Optional[SessionInfo] but avoid forward reference issue
        """Get session information by session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionInfo object or None if not found
        """
        if not REDIS_AVAILABLE:
            return None
            
        try:
            client = await self._get_redis()
            session_key = f"{self.key_prefix}{session_id}"
            
            session_data = await client.hgetall(session_key)
            
            if not session_data or not session_data.get("is_active", "True").lower() == "true":
                return None
            
            # Update last accessed time
            now = datetime.utcnow()
            await client.hset(session_key, "last_accessed", now.isoformat())
            await client.expire(session_key, self.session_ttl)  # Refresh TTL
            
            return SessionInfo(
                session_id=session_id,
                user_id=int(session_data["user_id"]),
                user_agent=session_data.get("user_agent"),
                ip_address=session_data.get("ip_address"),
                device_name=session_data.get("device_name"),
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_accessed=datetime.fromisoformat(session_data["last_accessed"]),
                expires_at=datetime.fromisoformat(session_data["expires_at"]),
                is_active=session_data.get("is_active", "True").lower() == "true"
            )
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: int) -> List[SessionInfo]:
        """Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of SessionInfo objects
        """
        if not REDIS_AVAILABLE:
            return []
            
        try:
            client = await self._get_redis()
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            
            session_ids = await client.smembers(user_sessions_key)
            sessions = []
            
            for session_id in session_ids:
                session_info = await self.get_session(session_id)
                if session_info and session_info.is_active:
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
            return []
    
    async def update_session_access(self, session_id: str) -> bool:
        """Update the last accessed time for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        if not REDIS_AVAILABLE:
            return False
            
        try:
            client = await self._get_redis()
            session_key = f"{self.key_prefix}{session_id}"
            
            # Check if session exists and is active
            is_active = await client.hget(session_key, "is_active")
            if not is_active or is_active.lower() != "true":
                return False
            
            # Update last accessed time
            now = datetime.utcnow()
            await client.hset(session_key, "last_accessed", now.isoformat())
            await client.expire(session_key, self.session_ttl)  # Refresh TTL
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session access {session_id}: {str(e)}")
            return False
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session.
        
        Args:
            session_id: Session ID to revoke
            
        Returns:
            True if successful, False otherwise
        """
        if not REDIS_AVAILABLE:
            return False
            
        try:
            client = await self._get_redis()
            session_key = f"{self.key_prefix}{session_id}"
            
            # Get user_id before deleting the session
            user_id_str = await client.hget(session_key, "user_id")
            if user_id_str:
                user_id = int(user_id_str)
                
                # Remove session from user's session list
                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                await client.srem(user_sessions_key, session_id)
            
            # Mark as inactive instead of deleting to preserve history
            await client.hset(session_key, "is_active", "false")
            
            logger.info(f"Revoked session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {str(e)}")
            return False
    
    async def revoke_all_user_sessions(self, user_id: int) -> int:
        """Revoke all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions revoked
        """
        if not REDIS_AVAILABLE:
            return 0
            
        try:
            client = await self._get_redis()
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            
            session_ids = await client.smembers(user_sessions_key)
            revoked_count = 0
            
            for session_id in session_ids:
                if await self.revoke_session(session_id):
                    revoked_count += 1
            
            logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Error revoking all sessions for user {user_id}: {str(e)}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of expired sessions cleaned up
        """
        if not REDIS_AVAILABLE:
            return 0
            
        try:
            client = await self._get_redis()
            
            # Find all session keys
            session_keys = await client.keys(f"{self.key_prefix}*")
            expired_count = 0
            
            for session_key in session_keys:
                # Check if session has expired
                expires_at_str = await client.hget(session_key, "expires_at")
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        if datetime.utcnow() > expires_at:
                            # Session has expired, remove it
                            session_id = session_key[len(self.key_prefix):]
                            
                            # Also remove from user's session list
                            user_id_str = await client.hget(session_key, "user_id")
                            if user_id_str:
                                user_id = int(user_id_str)
                                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                                await client.srem(user_sessions_key, session_id)
                            
                            await client.delete(session_key)
                            expired_count += 1
                    except ValueError:
                        # Invalid date format, remove the session
                        await client.delete(session_key)
                        expired_count += 1
            
            logger.info(f"Cleaned up {expired_count} expired sessions")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    async def health_check(self) -> Dict[str, any]:
        """Check Redis connection health.
        
        Returns:
            Health status dictionary
        """
        health = {
            "healthy": False,
            "backend": "redis" if REDIS_AVAILABLE else "disabled",
            "redis_available": REDIS_AVAILABLE,
        }
        
        if not REDIS_AVAILABLE:
            return health
        
        try:
            client = await self._get_redis()
            await client.ping()
            health["healthy"] = True
            health["connection_ok"] = True
        except Exception as e:
            logger.error(f"Session manager health check failed: {e}")
            health["error"] = str(e)
        
        return health


# Global session manager instance
_session_manager: Optional[RedisSessionManager] = None


def get_session_manager() -> RedisSessionManager:
    """Get or create global session manager instance.
    
    Returns:
        RedisSessionManager instance
    """
    global _session_manager
    
    if _session_manager is None:
        # Get Redis configuration from environment
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        session_ttl = int(os.getenv("SESSION_TTL_SECONDS", "86400"))  # 24 hours default
        
        _session_manager = RedisSessionManager(
            redis_url=redis_url,
            session_ttl=session_ttl
        )
    
    return _session_manager