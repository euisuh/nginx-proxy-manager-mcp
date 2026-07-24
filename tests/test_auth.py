import anyio
from starlette.responses import JSONResponse

from auth import BearerTokenAuthMiddleware
from server import get_sse_middleware


async def ok_app(scope, receive, send):
    response = JSONResponse({"ok": True})
    await response(scope, receive, send)


async def collect_response(app, headers=None):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http",
            "method": "GET",
            "path": "/sse",
            "headers": headers or [],
        },
        receive,
        send,
    )
    return messages


def response_status(messages):
    return next(message["status"] for message in messages if message["type"] == "http.response.start")


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


def test_get_sse_middleware_disabled_without_token(monkeypatch):
    monkeypatch.delenv("MCP_BEARER_TOKEN", raising=False)
    assert get_sse_middleware() == []


def test_get_sse_middleware_enabled_with_token(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", "secret")
    middleware = get_sse_middleware()
    assert len(middleware) == 1
    assert middleware[0].cls is BearerTokenAuthMiddleware
    assert middleware[0].kwargs == {"token": "secret"}
