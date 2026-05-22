"""
auth/dependencies.py — FastAPI Security Dependencies
Provides get_current_user and role-based access guard factories.
"""

from typing import Union
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database.database import get_db
from backend.app.auth.jwt_handler import decode_access_token
from backend.app.models.student import Student
from backend.app.models.faculty import Faculty

# OAuth2 scheme — token is expected at /login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> Union[Student, Faculty]:
    """
    Decode the JWT bearer token and return the matching user object.
    Raises 401 if the token is invalid or the user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    role: str = payload.get("role")
    if user_id_str is None or role is None:
        raise credentials_exception

    # Cast string from JWT payload to UUID for SQLAlchemy comparison
    try:
        import uuid as _uuid
        user_id = _uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception

    # Look up user in the correct table based on role
    if role in ("student",):
        result = await db.execute(select(Student).where(Student.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Faculty).where(Faculty.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: str):
    """
    Factory that returns a dependency enforcing role-based access.

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(
        current_user: Annotated[Union[Student, Faculty], Depends(get_current_user)]
    ):
        # .value converts enum to string for comparison with allowed_roles strings
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}",
            )
        return current_user

    return role_checker


# ── Convenience aliases ────────────────────────────────────────────────────────
CurrentUser = Annotated[Union[Student, Faculty], Depends(get_current_user)]
