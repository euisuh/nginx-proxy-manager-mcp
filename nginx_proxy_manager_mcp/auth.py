from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class HealthCheckMiddleware:
    """Serve an unauthenticated liveness endpoint for SSE deployments."""

    def __init__(self, app: ASGIApp, path: str = "/healthz") -> None:
        self.app = app
        self.path = path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("path") == self.path:
            response = JSONResponse({"ok": True, "service": "nginx-proxy-manager-mcp"})
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class BearerTokenAuthMiddleware:
    """Require a static bearer token for HTTP/SSE MCP transports."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        expected = f"Bearer {self.token}"
        provided = headers.get("authorization", "")
        if not secrets.compare_digest(provided, expected):
            response = JSONResponse(
                {"error": "unauthorized", "detail": "Missing or invalid bearer token"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
