"""
Role-Based Access Control (RBAC) module for dual user registration system.
Provides decorators and middleware for role-based endpoint protection.
"""

from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import HTTPException, status, Depends
from modules.auth import get_current_user


class RoleBasedAccessControl:
    """Role-based access control utilities."""
    
    @staticmethod
    def require_role(allowed_roles: List[str]):
        """
        Decorator to require specific user roles for endpoint access.
        
        Args:
            allowed_roles: List of roles that are allowed to access the endpoint
            
        Returns:
            Decorator function
            
        Example:
            @require_role(["practitioner", "admin"])
            async def practitioner_only_endpoint():
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current_user from kwargs or get it
                current_user = kwargs.get('current_user')
                if current_user is None:
                    # If not provided, get it from dependency
                    current_user = await get_current_user()
                
                user_role = current_user.role
                
                if user_role not in allowed_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {allowed_roles}. Your role: {user_role}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_verification_status(allowed_statuses: List[str]):
        """
        Decorator to require specific verification statuses for endpoint access.
        
        Args:
            allowed_statuses: List of verification statuses that are allowed
            
        Returns:
            Decorator function
            
        Example:
            @require_verification_status(["verified", "active"])
            async def verified_only_endpoint():
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current_user from kwargs or get it
                current_user = kwargs.get('current_user')
                if current_user is None:
                    # If not provided, get it from dependency
                    current_user = await get_current_user()
                
                user_status = current_user.verification_status
                
                if user_status not in allowed_statuses:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required verification status: {allowed_statuses}. Your status: {user_status}"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_verified_practitioner():
        """
        Decorator to require verified practitioner status for endpoint access.
        Combines role and verification status checks.
        
        Returns:
            Decorator function
            
        Example:
            @require_verified_practitioner()
            async def verified_practitioner_endpoint():
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current_user from kwargs or get it
                current_user = kwargs.get('current_user')
                if current_user is None:
                    # If not provided, get it from dependency
                    current_user = await get_current_user()
                
                user_role = current_user.role
                user_status = current_user.verification_status
                
                if user_role != "practitioner":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. This endpoint requires practitioner role."
                    )
                
                if user_status not in ["verified", "active"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. This endpoint requires verified practitioner status."
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_admin():
        """
        Decorator to require admin privileges for endpoint access.
        
        Returns:
            Decorator function
            
        Example:
            @require_admin()
            async def admin_only_endpoint():
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current_user from kwargs or get it
                current_user = kwargs.get('current_user')
                if current_user is None:
                    # If not provided, get it from dependency
                    current_user = await get_current_user()
                
                if not current_user.is_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied. This endpoint requires admin privileges."
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Convenience functions for FastAPI dependencies
def require_user_role(current_user = Depends(get_current_user)):
    """FastAPI dependency to require user role."""
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires user role."
        )
    return current_user


def require_practitioner_role(current_user = Depends(get_current_user)):
    """FastAPI dependency to require practitioner role."""
    if current_user.role != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires practitioner role."
        )
    return current_user


def require_verified_practitioner_dependency(current_user = Depends(get_current_user)):
    """FastAPI dependency to require verified practitioner."""
    if current_user.role != "practitioner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires practitioner role."
        )
    
    if current_user.verification_status not in ["verified", "active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires verified practitioner status."
        )
    
    return current_user


def require_admin_dependency(current_user = Depends(get_current_user)):
    """FastAPI dependency to require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This endpoint requires admin privileges."
        )
    return current_user


# Create convenience instances
rbac = RoleBasedAccessControl()
require_role = rbac.require_role
require_verification_status = rbac.require_verification_status
require_verified_practitioner = rbac.require_verified_practitioner
require_admin = rbac.require_admin