import anyio
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.responses import JSONResponse

from nginx_proxy_manager_mcp.auth import BearerTokenAuthMiddleware, HealthCheckMiddleware
from nginx_proxy_manager_mcp.server import get_sse_middleware


async def ok_app(scope, receive, send):
    response = JSONResponse({"ok": True})
    await response(scope, receive, send)


def apply_middleware(app, middleware):
    app = ExceptionMiddleware(app)
    for item in reversed(middleware):
        app = item.cls(app, **item.kwargs)
    return app


async def collect_response(app, headers=None, path="/sse"):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": headers or [],
        },
        receive,
        send,
    )
    return messages


def response_status(messages):
    return next(message["status"] for message in messages if message["type"] == "http.response.start")


def test_health_check_returns_ok():
    app = HealthCheckMiddleware(ok_app)
    messages = anyio.run(collect_response, app, None, "/healthz")
    assert response_status(messages) == 200


def test_bearer_auth_rejects_missing_header():
    app = BearerTokenAuthMiddleware(ok_app, token="secret")
    messages = anyio.run(collect_response, app)
    assert response_status(messages) == 401


def test_bearer_auth_rejects_wrong_token():
    app = BearerTokenAuthMiddleware(ok_app, token="secret")
    messages = anyio.run(
        collect_response,
        app,
        [(b"authorization", b"Bearer wrong")],
    )
    assert response_status(messages) == 401


def test_bearer_auth_accepts_correct_token():
    app = BearerTokenAuthMiddleware(ok_app, token="secret")
    messages = anyio.run(
        collect_response,
        app,
        [(b"authorization", b"Bearer secret")],
    )
    assert response_status(messages) == 200


def test_get_sse_middleware_includes_health_check_without_token(monkeypatch):
    monkeypatch.delenv("MCP_BEARER_TOKEN", raising=False)
    middleware = get_sse_middleware()
    assert len(middleware) == 1
    assert middleware[0].cls is HealthCheckMiddleware


def test_get_sse_middleware_enabled_with_token(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", "secret")
    middleware = get_sse_middleware()
    assert len(middleware) == 2
    assert middleware[0].cls is HealthCheckMiddleware
    assert middleware[1].cls is BearerTokenAuthMiddleware
    assert middleware[1].kwargs == {"token": "secret"}


def test_health_check_bypasses_bearer_auth_when_enabled(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", "secret")
    app = apply_middleware(ok_app, get_sse_middleware())
    messages = anyio.run(collect_response, app, None, "/healthz")
    assert response_status(messages) == 200
