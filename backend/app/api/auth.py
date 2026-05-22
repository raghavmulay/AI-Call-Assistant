"""
routes/auth.py — Authentication Endpoints
POST /signup  — Register a new student or faculty member
POST /login   — Authenticate and receive a JWT token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database.database import get_db
from backend.app.schemas.auth import (
    StudentSignupRequest,
    FacultySignupRequest,
    LoginRequest,
    TokenResponse,
)
from backend.app.models.student import Student, Role
from backend.app.models.faculty import Faculty, FacultyRole
from backend.app.auth.hashing import hash_password, verify_password
from backend.app.auth.jwt_handler import create_access_token
from backend.app.services.student_service import get_student_by_email
from backend.app.services.faculty_service import get_faculty_by_email

router = APIRouter(prefix="", tags=["Authentication"])


# ── POST /signup/student ──────────────────────────────────────────────────────
@router.post(
    "/signup/student",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
async def signup_student(
    data: StudentSignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new student.

    - **email** must be unique
    - **password** minimum 8 characters
    - Returns JWT token immediately so the user is logged in after signup
    """
    # Check email uniqueness across both tables
    if await get_student_by_email(data.email, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    student = Student(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        branch=data.branch,
        year=data.year,
        division=data.division,
        cgpa=data.cgpa,
        role=Role.student,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)

    token = create_access_token({"sub": str(student.id), "role": student.role.value})
    return TokenResponse(access_token=token, role=student.role.value, user_id=student.id)


# ── POST /signup/faculty ──────────────────────────────────────────────────────
@router.post(
    "/signup/faculty",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new faculty/admin account",
)
async def signup_faculty(
    data: FacultySignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new faculty or admin account."""
    if await get_faculty_by_email(data.email, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    faculty = Faculty(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        department=data.department,
        role=FacultyRole(data.role),
    )
    db.add(faculty)
    await db.flush()
    await db.refresh(faculty)

    token = create_access_token({"sub": str(faculty.id), "role": faculty.role.value})
    return TokenResponse(access_token=token, role=faculty.role.value, user_id=faculty.id)


# ── POST /login ───────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email, password, and role.

    - **role**: must be `student`, `faculty`, or `admin`
    - Returns a Bearer token to use in the Authorization header
    """
    invalid_creds = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if data.role == "student":
        user = await get_student_by_email(data.email, db)
    else:
        user = await get_faculty_by_email(data.email, db)

    if user is None or not verify_password(data.password, user.hashed_password):
        raise invalid_creds

    # Ensure the role in the DB matches the requested role
    if user.role.value != data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account is not registered as '{data.role}'.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token, role=user.role.value, user_id=user.id)
