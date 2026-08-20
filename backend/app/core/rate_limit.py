"""
Shared slowapi Limiter instance. Keyed by client IP address, which is the
right key for pre-auth endpoints like /auth/login where we don't have a
user_id yet to key on.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
