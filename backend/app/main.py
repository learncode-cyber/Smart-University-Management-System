"""
FastAPI application entrypoint. Run locally with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.v1.auth import router as auth_router
from app.api.v1.academic import router as academic_router
from app.api.v1.users import router as users_router
from app.api.v1.exams import router as exams_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.results import router as results_router
from app.api.v1.fees import router as fees_router
from app.api.v1.schedule import router as schedule_router
from app.api.v1.notifications import router as notifications_router
from app.core.errors import AppError, app_error_handler
from app.core.rate_limit import limiter

app = FastAPI(
    title="University Management System API",
    version="0.1.0",
    description="REST API for the University Management System — see /docs for the "
                 "interactive OpenAPI/Swagger documentation.",
)

# CORS middleware: allow frontend dev server (localhost:5173) and any origin via
# the Vite proxy. The proxy on port 5173 runs the dev server inside the frontend
# container; for browser requests to succeed, the backend must accept that origin.
# In production, this should be restricted to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(academic_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(exams_router, prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")
app.include_router(results_router, prefix="/api/v1")
app.include_router(fees_router, prefix="/api/v1")
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")


@app.get("/health", tags=["System"], summary="Health check")
def health_check():
    return {"status": "ok"}
