import pytest
import respx
import httpx
from npm_client import NPMClient


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
def test_get_raises_on_non_401_error():
    respx.post("http://npm.test/api/tokens").mock(
        return_value=httpx.Response(200, json={"token": "tok"})
    )
    respx.get("http://npm.test/api/nginx/proxy-hosts").mock(
        return_value=httpx.Response(500)
    )
    client = NPMClient()
    with pytest.raises(httpx.HTTPStatusError):
        client.get("/nginx/proxy-hosts")


@respx.mock
def test_missing_env_raises(monkeypatch):
    monkeypatch.delenv("NPM_URL")
    with pytest.raises(KeyError):
        NPMClient()
