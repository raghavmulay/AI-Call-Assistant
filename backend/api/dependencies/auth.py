"""
api/dependencies/auth.py — FastAPI auth dependencies.

get_current_user   → raises 401 if no valid token
get_optional_user  → returns user_id or None (guest allowed)
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[str]:
    """Returns user_id string if authenticated, None for guests."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    return payload.get("sub") if payload else None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """Raises 401 if not authenticated."""
    user_id = get_optional_user(credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
