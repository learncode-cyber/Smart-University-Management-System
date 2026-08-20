"""
Auth router — /api/v1/auth/*

Thin layer: parse request -> call service -> shape response. All the
actual logic (token issuing, rotation, revocation) lives in
services/auth_service.py, per the layered-architecture standard.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse,
    LogoutRequest, ChangePasswordRequest, MessageResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
    description="Returns a short-lived access token and a long-lived refresh token. "
                "The access token is a stateless JWT; the refresh token is tracked "
                "server-side so it can be revoked on logout or password change.",
)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login_endpoint(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user, access_token, raw_refresh = auth_service.login(
        db,
        email=body.email,
        password=body.password,
        university_id=settings.DEFAULT_UNIVERSITY_ID,  # single-university build phase — see auth_service.login docstring
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Exchange a refresh token for a new access token",
    description="Rotates the refresh token: the one supplied is invalidated and a "
                "new one is returned alongside the new access token.",
)
def refresh_endpoint(request: Request, body: RefreshRequest, db: Session = Depends(get_db)):
    access_token, new_raw_refresh = auth_service.refresh_access_token(
        db,
        raw_refresh_token=body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    # NOTE: the new refresh token is returned in the body here for
    # simplicity. In production, prefer setting it as an HttpOnly, Secure,
    # SameSite=strict cookie instead of JSON, so frontend JS never touches
    # the raw refresh token at all. Flagging this as a hardening step for
    # the deployment part (Part 11) rather than blocking this part on it.
    return AccessTokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out and revoke the given refresh token",
)
def logout_endpoint(
    body: LogoutRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    auth_service.logout(db, raw_refresh_token=body.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.put(
    "/password",
    response_model=MessageResponse,
    summary="Change own password",
    description="Requires the current password for confirmation. On success, all "
                "other active sessions (refresh tokens) for this account are revoked.",
)
def change_password_endpoint(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.change_password(
        db, current_user, current_password=body.current_password, new_password=body.new_password
    )
    return MessageResponse(message="Password changed successfully. Please log in again on other devices.")
