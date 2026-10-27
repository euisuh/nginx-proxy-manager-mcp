"""Calls go through the MCP protocol layer (FastMCP in-memory client) to a real
NPMClient whose HTTP traffic is mocked with respx."""
import asyncio

import httpx
import pytest
import respx
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from nginx_proxy_manager_mcp.npm_client import NPMClient
from nginx_proxy_manager_mcp.server import register_all

NPM = "http://npm.test/api"


@pytest.fixture
def npm(monkeypatch):
    monkeypatch.setenv("NPM_URL", "http://npm.test")
    monkeypatch.setenv("NPM_EMAIL", "admin@test.com")
    monkeypatch.setenv("NPM_PASSWORD", "testpass")
    with respx.mock(assert_all_called=False) as mock:
        mock.post(f"{NPM}/tokens").mock(return_value=httpx.Response(200, json={"token": "jwt"}))
        mock.get(f"{NPM}/").mock(return_value=httpx.Response(
            200, json={"status": "OK", "version": {"major": 2, "minor": 16, "revision": 0}},
        ))
        yield mock


def call(tool, args, read_only=False):
    mcp = FastMCP("e2e")
    register_all(mcp, NPMClient(), read_only)

    async def run():
        async with Client(mcp) as client:
            return await client.call_tool(tool, args)

    return asyncio.run(run())


def test_wildcard_dns_certificate_end_to_end(npm):
    route = npm.post(f"{NPM}/nginx/certificates").mock(
        return_value=httpx.Response(201, json={"id": 9, "provider": "letsencrypt"}),
    )
    result = call("create_letsencrypt_cert", {
        "domain_names": ["*.example.com"],
        "dns_challenge": True,
        "dns_provider": "cloudflare",
        "dns_provider_credentials": "dns_cloudflare_api_token = s3cret",
    })
    assert result.data["id"] == 9
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer jwt"
    assert b'"letsencrypt_email"' not in sent.content


def test_get_access_list_end_to_end(npm):
    route = npm.get(f"{NPM}/nginx/access-lists/3").mock(return_value=httpx.Response(200, json={
        "id": 3, "name": "lan", "clients": [], "items": [{"username": "a", "password": "", "hint": "x***"}],
    }))
    result = call("get_access_list", {"id": 3})
    assert route.calls.last.request.url.params["expand"] == "items,clients"
    assert "hint" not in result.data["items"][0]


def test_npm_error_reaches_client_with_message(npm):
    npm.get(f"{NPM}/nginx/proxy-hosts/4").mock(return_value=httpx.Response(
        404, json={"error": {"code": 404, "message": "Not Found - 4"}},
    ))
    with pytest.raises(ToolError, match="HTTP 404: Not Found - 4"):
        call("get_proxy_host", {"id": 4})


def test_validation_error_sends_nothing(npm):
    route = npm.post(f"{NPM}/nginx/proxy-hosts")
    with pytest.raises(ToolError, match="forward_port"):
        call("create_proxy_host", {
            "domain_names": ["a.example.com"], "forward_scheme": "http",
            "forward_host": "app", "forward_port": 70000,
        })
    assert not route.called


def test_read_only_mode_hides_mutating_tools(npm):
    with pytest.raises(ToolError):
        call("delete_certificate", {"id": 1}, read_only=True)
