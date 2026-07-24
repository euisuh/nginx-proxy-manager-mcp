import pytest


def test_validate_env_fails_on_missing_vars(monkeypatch):
    monkeypatch.delenv("NPM_URL", raising=False)
    monkeypatch.delenv("NPM_EMAIL", raising=False)
    monkeypatch.delenv("NPM_PASSWORD", raising=False)
    from nginx_proxy_manager_mcp.server import validate_env
    with pytest.raises(SystemExit) as exc:
        validate_env()
    assert exc.value.code == 1


def test_validate_env_passes_with_all_vars(monkeypatch):
    monkeypatch.setenv("NPM_URL", "http://npm.test")
    monkeypatch.setenv("NPM_EMAIL", "admin@test.com")
    monkeypatch.setenv("NPM_PASSWORD", "testpass")
    from nginx_proxy_manager_mcp.server import validate_env
    validate_env()  # should not raise


def test_get_transport_defaults_to_sse(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    from nginx_proxy_manager_mcp.server import get_transport
    assert get_transport() == "sse"


def test_get_transport_accepts_stdio(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "stdio")
    from nginx_proxy_manager_mcp.server import get_transport
    assert get_transport() == "stdio"


def test_get_transport_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "websocket")
    from nginx_proxy_manager_mcp.server import get_transport
    with pytest.raises(SystemExit) as exc:
        get_transport()
    assert exc.value.code == 1


def test_get_host_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    from nginx_proxy_manager_mcp.server import get_host
    assert get_host() == "127.0.0.1"


def test_get_host_uses_env_value(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    from nginx_proxy_manager_mcp.server import get_host
    assert get_host() == "0.0.0.0"
