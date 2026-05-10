"""Rate limit keying (SlowAPI) — isolated from auth rules."""

from app.modules.rate_limit.keys import rate_limit_key

__all__ = ["rate_limit_key"]
