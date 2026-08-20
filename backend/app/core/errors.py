"""
Standardized error responses.

Every error from this API — auth failures, validation errors, not-found,
permission-denied — comes back in the SAME shape:

    {
      "error": {
        "code": "INVALID_CREDENTIALS",
        "message": "Email or password is incorrect."
      }
    }

`code` is machine-readable (frontend can switch on it, e.g. to redirect
to login on AUTH_TOKEN_EXPIRED without inspecting free-text). `message`
is what gets shown to the human. This is registered as a FastAPI
exception handler in main.py so raising `AppError(...)` anywhere in the
codebase automatically produces this shape.
"""
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Raise this anywhere in routers/services instead of a bare HTTPException
    when you want the standardized {error: {code, message}} body."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


# --- common, reusable error instances/factories for auth ---

def invalid_credentials() -> AppError:
    return AppError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")


def token_expired() -> AppError:
    return AppError(401, "TOKEN_EXPIRED", "Your session has expired. Please log in again.")


def token_invalid() -> AppError:
    return AppError(401, "TOKEN_INVALID", "Invalid authentication token.")


def account_inactive() -> AppError:
    return AppError(403, "ACCOUNT_INACTIVE", "This account has been deactivated.")


def insufficient_permissions() -> AppError:
    return AppError(403, "INSUFFICIENT_PERMISSIONS", "You do not have permission to perform this action.")


def refresh_token_invalid() -> AppError:
    return AppError(401, "REFRESH_TOKEN_INVALID", "Refresh token is invalid, expired, or already used.")


def wrong_current_password() -> AppError:
    return AppError(400, "WRONG_CURRENT_PASSWORD", "Current password is incorrect.")
