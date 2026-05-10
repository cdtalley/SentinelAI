"""Request key for rate limit buckets (no raw secrets in logs)."""

from __future__ import annotations

import hashlib

from fastapi import Request
from slowapi.util import get_remote_address


def rate_limit_key(request: Request) -> str:
    token = request.headers.get("X-API-Key")
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    if token:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:40]
        return f"key:{digest}"
    return f"ip:{get_remote_address(request)}"
