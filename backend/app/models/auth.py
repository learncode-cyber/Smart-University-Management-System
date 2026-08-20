"""
RefreshToken — the stateful half of our hybrid token strategy.

We never store the raw refresh token string, only its SHA-256 hash
(`token_hash`). This mirrors how we store passwords: if the database is
ever leaked, the tokens inside it are useless to an attacker without
also knowing the original random string, which never touches disk.

`revoked_at` being non-null means the token is dead — used for both
explicit logout AND refresh-token rotation (see services/auth_service.py:
every successful /auth/refresh call revokes the old token and issues a
new one, so a stolen-but-unused refresh token becomes invalid the moment
the legitimate user refreshes again).
"""
from datetime import datetime

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user_revoked", "user_id", "revoked_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # sha256 hex digest
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column()

    # lightweight device/session context, useful later for a "your active
    # sessions" security screen — not required by the proposal but nearly
    # free to capture now
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))

    user: Mapped["User"] = relationship()
