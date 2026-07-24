import pytest
import respx
import httpx
from nginx_proxy_manager_mcp.npm_client import NPMAPIError, NPMClient


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("NPM_URL", "http://npm.test")
    monkeypatch.setenv("NPM_EMAIL", "admin@test.com")
    monkeypatch.setenv("NPM_PASSWORD", "testpass")


@respx.mock
def test_authenticate_on_first_request():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "tok123"})
    )
    respx.get("http://npm.test/api/nginx/proxy-hosts").mock(
        return_value=httpx.Response(200, json=[])
    )
    client = NPMClient()
    assert client.token is None
    result = client.get("/nginx/proxy-hosts")
    assert result == []
    assert client.token == "tok123"


@respx.mock
def test_reauth_on_401():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "new-tok"})
    )
    call_count = 0

    def hosts_handler(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(401)
        return httpx.Response(200, json=[{"id": 1}])

    respx.get("http://npm.test/api/nginx/proxy-hosts").mock(side_effect=hosts_handler)
    client = NPMClient()
    client.token = "expired"
    result = client.get("/nginx/proxy-hosts")
    assert result == [{"id": 1}]
    assert call_count == 2


@respx.mock
def test_get_raises_structured_error_on_non_401_error():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "tok"})
    )
    respx.get("http://npm.test/api/nginx/proxy-hosts").mock(
        return_value=httpx.Response(500, json={"message": "database unavailable"})
    )
    client = NPMClient()
    with pytest.raises(NPMAPIError) as exc:
        client.get("/nginx/proxy-hosts")
    assert exc.value.method == "GET"
    assert exc.value.path == "/nginx/proxy-hosts"
    assert exc.value.status_code == 500
    assert "database unavailable" in str(exc.value)


@respx.mock
def test_missing_env_raises(monkeypatch):
    monkeypatch.delenv("NPM_URL")
    with pytest.raises(KeyError):
        NPMClient()


@respx.mock
def test_second_401_raises_structured_error():
    """Second 401 after re-auth must raise, not loop."""
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "new-tok"})
    )
    respx.get("http://npm.test/api/nginx/proxy-hosts").mock(
        return_value=httpx.Response(401)
    )
    client = NPMClient()
    client.token = "expired"
    with pytest.raises(NPMAPIError) as exc:
        client.get("/nginx/proxy-hosts")
    assert exc.value.status_code == 401


@respx.mock
def test_missing_email_env_raises(monkeypatch):
    monkeypatch.delenv("NPM_EMAIL")
    with pytest.raises(KeyError):
        NPMClient()


@respx.mock
def test_authentication_error_is_structured_and_redacted():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(401, json={"error": "bad credentials"})
    )
    client = NPMClient()
    with pytest.raises(NPMAPIError) as exc:
        client.get("/nginx/proxy-hosts")
    assert exc.value.method == "POST"
    assert exc.value.path == "/tokens"
    assert exc.value.status_code == 401
    assert "bad credentials" in str(exc.value)
    assert "testpass" not in str(exc.value)


@respx.mock
def test_error_with_non_json_body_uses_response_text():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "tok"})
    )
    respx.get("http://npm.test/api/nginx/proxy-hosts").mock(
        return_value=httpx.Response(502, text="bad gateway")
    )
    client = NPMClient()
    with pytest.raises(NPMAPIError) as exc:
        client.get("/nginx/proxy-hosts")
    assert "bad gateway" in str(exc.value)
