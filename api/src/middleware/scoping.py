import uuid
from typing import Callable

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.schemas import ScopeHeaders

EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    f"{settings.api_prefix}/register",
}


def parse_scope_headers(request: Request) -> ScopeHeaders:
    user_raw = request.headers.get("X-User-Id")
    profile_raw = request.headers.get("X-Profile-Id")
    tenant_raw = request.headers.get("X-Tenant-Id")

    if not user_raw or not profile_raw:
        raise HTTPException(
            status_code=401,
            detail="Missing required headers: X-User-Id and X-Profile-Id",
        )

    try:
        user_id = uuid.UUID(user_raw)
        profile_id = uuid.UUID(profile_raw)
        tenant_id = uuid.UUID(tenant_raw) if tenant_raw else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid UUID in scope headers") from exc

    return ScopeHeaders(user_id=user_id, profile_id=profile_id, tenant_id=tenant_id)


class ScopingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path.rstrip("/") or "/"
        if request.method == "OPTIONS":
            return await call_next(request)

        exempt = path in EXEMPT_PATHS or path.startswith("/docs")
        if not exempt and path.startswith(settings.api_prefix):
            scope = parse_scope_headers(request)
            request.state.scope = scope

        return await call_next(request)
