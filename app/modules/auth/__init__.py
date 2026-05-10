"""Authentication backends (API key today; extend with JWT/OIDC modules here)."""

from app.modules.auth.dependencies import require_client_auth, verify_ws_api_key

__all__ = ["require_client_auth", "verify_ws_api_key"]
