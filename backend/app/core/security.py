"""
Security primitives: password hashing (bcrypt) and JWT encode/decode.

Kept as pure, dependency-free functions (no DB access here) so they're
trivially unit-testable and so the auth service can compose them without
this module needing to know about SQLAlchemy sessions at all.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt has a hard 72-byte input limit; passlib handles truncation
# warnings for us, but we still cap length at the schema layer (Part 3)
# to avoid silently truncating a user's intended password.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: int, role: str, university_id: int) -> str:
    """Short-lived, stateless JWT. Never stored in the DB — verified only
    by signature + expiry check."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "university_id": university_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jose.JWTError if signature is invalid or token is expired —
    callers (get_current_user) are responsible for turning that into a
    proper 401 response."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_refresh_token() -> tuple[str, str]:
    """
    Returns (raw_token, token_hash).
    raw_token  -> sent to the client, never stored anywhere server-side.
    token_hash -> what we persist in refresh_tokens.token_hash, so a DB
                  leak alone can't be used to forge a session.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    """Used to look up an incoming refresh token by its hash."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
