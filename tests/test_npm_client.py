import pytest
import respx
import httpx
from nginx_proxy_manager_mcp.npm_client import NPMAPIError, NPMClient, NPMConnectionError


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


@respx.mock
def test_npm_nested_error_message_is_extracted():
    # NPM's express error handler responds with {"error": {"code": ..., "message": ...}}.
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "tok"})
    )
    respx.put("http://npm.test/api/nginx/proxy-hosts/1").mock(
        return_value=httpx.Response(
            400, json={"error": {"code": 400, "message": "data must NOT have additional properties"}}
        )
    )
    client = NPMClient()
    with pytest.raises(NPMAPIError) as exc:
        client.put("/nginx/proxy-hosts/1", json={})
    assert exc.value.detail == "data must NOT have additional properties"


@respx.mock
def test_connection_error_is_actionable_and_redacted():
    respx.post("http://npm.test/api/tokens").mock(side_effect=httpx.ConnectError("refused"))
    client = NPMClient()
    with pytest.raises(NPMConnectionError) as exc:
        client.get("/nginx/proxy-hosts")
    message = str(exc.value)
    assert "http://npm.test" in message and "refused" in message
    assert "testpass" not in message


@respx.mock
def test_token_is_sent_only_in_authorization_header():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "secret-jwt"})
    )
    route = respx.get("http://npm.test/api/nginx/streams").mock(
        return_value=httpx.Response(200, json=[])
    )
    NPMClient().get("/nginx/streams")
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer secret-jwt"
    assert "secret-jwt" not in str(request.url)


@respx.mock
def test_npm_version_is_read_once_without_auth():
    route = respx.get("http://npm.test/api/").mock(
        return_value=httpx.Response(
            200, json={"status": "OK", "version": {"major": 2, "minor": 12, "revision": 6}}
        )
    )
    client = NPMClient()
    assert client.npm_version() == (2, 12)
    assert client.npm_version() == (2, 12)
    assert route.call_count == 1
    assert "authorization" not in route.calls.last.request.headers
    assert client.token is None


@respx.mock
def test_npm_version_missing_defaults_to_current_schema():
    respx.get("http://npm.test/api/").mock(return_value=httpx.Response(200, json={"status": "OK"}))
    assert NPMClient().npm_version() >= (2, 13)


@respx.mock
def test_empty_success_body_returns_none():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "tok"})
    )
    respx.post("http://npm.test/api/nginx/proxy-hosts/1/enable").mock(
        return_value=httpx.Response(200)
    )
    assert NPMClient().post("/nginx/proxy-hosts/1/enable") is None
