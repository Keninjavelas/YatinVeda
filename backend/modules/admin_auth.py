"""Admin authorization dependencies for protected endpoints."""

from fastapi import HTTPException, status, Depends
from modules.auth import get_current_user


async def require_admin(current_user=Depends(get_current_user)):
    """Dependency that ensures the current user has admin privileges.
    
    Raises:
        HTTPException: 403 if user is not an admin
        
    Returns:
        The current user object with confirmed admin status
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )
    return current_user
