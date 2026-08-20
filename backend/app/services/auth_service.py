"""
Auth business logic — kept OUT of the router (routers only parse
requests, call this, and shape responses; see the "never business logic
inside route handlers" standard from Part 0).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import invalid_credentials, refresh_token_invalid, wrong_current_password
from app.core.security import (
    verify_password, hash_password, create_access_token,
    generate_refresh_token, hash_refresh_token,
)
from app.core.config import settings
from app.models.user import User
from app.models.auth import RefreshToken


def _issue_token_pair(db: Session, user: User, user_agent: str | None, ip_address: str | None):
    access_token = create_access_token(
        user_id=user.id, role=user.role.value, university_id=user.university_id
    )

    raw_refresh, refresh_hash = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    ))
    db.commit()

    return access_token, raw_refresh


def login(db: Session, email: str, password: str, university_id: int,
          user_agent: str | None = None, ip_address: str | None = None):
    """
    NOTE: `university_id` here is a placeholder parameter for the
    single-university build phase — the login form doesn't ask the user
    which university they belong to; we resolve it via
    settings.DEFAULT_UNIVERSITY_ID at the router layer. Once multi-tenancy
    goes live, login would resolve university from a subdomain or an
    explicit tenant selector instead.
    """
    stmt = select(User).where(User.university_id == university_id, User.email == email)
    user = db.scalar(stmt)

    if user is None or not verify_password(password, user.password_hash):
        # deliberately identical error for "no such user" and "wrong
        # password" — telling an attacker "that email doesn't exist" is
        # itself a leak (user enumeration).
        raise invalid_credentials()

    if not user.is_active:
        raise invalid_credentials()  # don't reveal "this account exists but is deactivated" pre-auth

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token, raw_refresh = _issue_token_pair(db, user, user_agent, ip_address)
    return user, access_token, raw_refresh


def refresh_access_token(db: Session, raw_refresh_token: str,
                          user_agent: str | None = None, ip_address: str | None = None):
    """
    Refresh-token ROTATION: the incoming token is revoked and a brand new
    one is issued on every call. If someone replays an already-used
    refresh token (e.g. a stolen one, after the real user already
    refreshed), it will be found already revoked and rejected here.
    """
    token_hash = hash_refresh_token(raw_refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    token_row = db.scalar(stmt)

    now = datetime.now(timezone.utc)
    if (
        token_row is None
        or token_row.revoked_at is not None
        or token_row.expires_at < now
    ):
        raise refresh_token_invalid()

    user = db.get(User, token_row.user_id)
    if user is None or not user.is_active:
        raise refresh_token_invalid()

    # rotate: kill the old token now, issue a fresh pair
    token_row.revoked_at = now
    db.commit()

    access_token, new_raw_refresh = _issue_token_pair(db, user, user_agent, ip_address)
    return access_token, new_raw_refresh


def logout(db: Session, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    token_row = db.scalar(stmt)

    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        db.commit()
    # if the token doesn't exist or is already revoked, logout is still
    # a no-op success from the client's point of view — nothing to leak here


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise wrong_current_password()

    user.password_hash = hash_password(new_password)
    db.commit()

    # security decision (flagged in the design discussion): revoke every
    # active refresh token for this user so a password change forces
    # re-login everywhere else the account might be signed in.
    now = datetime.now(timezone.utc)
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
    )
    for token_row in db.scalars(stmt):
        token_row.revoked_at = now
    db.commit()
