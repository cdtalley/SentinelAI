"""Process-local rate limiter (SlowAPI). Swap for Redis-backed limiter at the edge if needed."""

from __future__ import annotations

from slowapi import Limiter

from app.config import get_settings
from app.modules.rate_limit.keys import rate_limit_key

_cfg = get_settings()
_rpm = (
    _cfg.API_RATE_LIMIT_PER_MINUTE
    if _cfg.RATE_LIMIT_ENABLED
    else 999_999
)
limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=[f"{_rpm}/minute"],
)
