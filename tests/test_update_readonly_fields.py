import json

import pytest
import respx

from nginx_proxy_manager_mcp.npm_client import NPMClient
from nginx_proxy_manager_mcp.tools.access_lists import AccessListTools
from nginx_proxy_manager_mcp.tools.proxy_hosts import ProxyHostTools
from nginx_proxy_manager_mcp.tools.redirection_hosts import RedirectionHostTools
from nginx_proxy_manager_mcp.tools.streams import StreamTools


READ_ONLY = {
    "id": 11,
    "created_on": "2026-10-01T00:00:00Z",
    "modified_on": "2026-10-02T00:00:00Z",
    "owner_user_id": 1,
    "owner": {"id": 1},
    "certificate": {"id": 7},
    "access_list": {"id": 3},
    "unexpected_field": "reject me",
}

CASES = [
    (
        ProxyHostTools, "update_proxy_host", "proxy-hosts",
        {
            "domain_names": ["a.example.com"], "forward_scheme": "http",
            "forward_host": "app", "forward_port": 3000, "ssl_forced": False,
            "certificate_id": 7, "access_list_id": 3, "block_exploits": True,
            "caching_enabled": False, "allow_websocket_upgrade": True,
            "advanced_config": "proxy_read_timeout 90s;", "meta": {"custom": "keep"},
            "locations": [{"path": "/api", "forward_host": "api", "forward_port": 8080,
                           "forward_scheme": "http", "advanced_config": ""}],
            "hsts_enabled": True, "hsts_subdomains": False, "http2_support": True,
            "trust_forwarded_proto": True, "enabled": False,
        },
        {"ssl_forced": True}, {},
    ),
    (
        RedirectionHostTools, "update_redirection_host", "redirection-hosts",
        {
            "domain_names": ["a.example.com"], "forward_scheme": "https",
            "forward_domain_name": "b.example.com", "forward_http_code": 301,
            "preserve_path": True, "certificate_id": 7, "ssl_forced": False,
            "hsts_enabled": True, "hsts_subdomains": True, "http2_support": True,
            "block_exploits": True, "advanced_config": "# keep config",
            "meta": {"custom": "keep"},
        },
        {"preserve_path": False}, {"enabled": True},
    ),
    (
        StreamTools, "update_stream", "streams",
        {
            "incoming_port": 2222, "forwarding_host": "app", "forwarding_port": 22,
            "tcp_forwarding": True, "udp_forwarding": False, "certificate_id": 7,
            "meta": {"custom": "keep"},
        },
        {"forwarding_port": 2223}, {"enabled": True},
    ),
    (
        AccessListTools, "update_access_list", "access-lists",
        {
            "name": "Office", "satisfy_any": False, "pass_auth": True,
            "items": [{"username": "admin", "password": ""}],
            "clients": [{"address": "203.0.113.0/24", "directive": "allow"}],
        },
        {"name": "Renamed"},
        {"proxy_host_count": 2, "proxy_hosts": [{"id": 1}], "meta": {}},
    ),
]


@pytest.mark.parametrize("dry_run", [False, True], ids=["put", "dry-run"])
@pytest.mark.parametrize(
    "tool_class,method,resource,writable,updates,extra", CASES,
    ids=["proxy-host", "redirection-host", "stream", "access-list"],
)
def test_update_sends_only_writable_fields(
    monkeypatch, tool_class, method, resource, writable, updates, extra, dry_run,
):
    monkeypatch.setenv("NPM_URL", "http://npm.test")
    monkeypatch.setenv("NPM_EMAIL", "admin@test.com")
    monkeypatch.setenv("NPM_PASSWORD", "testpass")
    existing = {**READ_ONLY, **writable, **extra}
    if resource == "access-lists":
        for key in ("items", "clients"):
            existing[key] = [
                {**entry, "id": 9, "created_on": "...", "modified_on": "...",
                 "access_list_id": 11, "meta": {}, "hint": "a****"}
                for entry in writable[key]
            ]
    expected = {**writable, **updates}
    path = f"/nginx/{resource}/11"
    with respx.mock(assert_all_called=False) as router:
        get_route = router.get(f"http://npm.test/api{path}").respond(200, json=existing)
        put_route = router.put(f"http://npm.test/api{path}").respond(200, json={"id": 11})
        with NPMClient() as client:
            client.token = "test-token"
            result = getattr(tool_class(client), method)(11, **updates, dry_run=dry_run)
        assert get_route.call_count == 1
        if dry_run:
            assert result == {"dry_run": True, "method": "PUT", "path": path, "json": expected}
            assert not put_route.called
        else:
            assert result == {"id": 11}
            assert put_route.call_count == 1
            assert json.loads(put_route.calls.last.request.content) == expected
