"""auth/hashing.py — Password Hashing with bcrypt via passlib."""

from passlib.context import CryptContext

# Use bcrypt as the hashing scheme; auto-upgrades old hashes if needed
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password. Returns the bcrypt hash string."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain-text password against a stored bcrypt hash.
    Returns True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
