"""Record the real HTTPS workflow preview with all HTTP calls mocked."""

import json
import os
from unittest.mock import patch

import httpx
import respx

from nginx_proxy_manager_mcp.npm_client import NPMClient
from nginx_proxy_manager_mcp.tools.proxy_hosts import ProxyHostTools


with patch.dict(os.environ, {
    "NPM_URL": "http://npm.test",
    "NPM_EMAIL": "demo@example.com",
    "NPM_PASSWORD": "mock-only",
}), respx.mock(assert_all_mocked=True) as mock, NPMClient() as client:
    mock.get("http://npm.test/api/").mock(return_value=httpx.Response(
        200, json={"status": "OK", "version": {"major": 2, "minor": 16, "revision": 0}},
    ))
    tools = ProxyHostTools(client)
    print("Mocked NPM API; no real credentials or network requests.\n")
    print('create_proxy_host_with_letsencrypt(')
    print('    domain_names=["blog.example.com"], forward_scheme="http",')
    print('    forward_host="app", forward_port=3000,')
    print('    dry_run=True)\n')
    preview = tools.create_proxy_host_with_letsencrypt(
        domain_names=["blog.example.com"],
        forward_scheme="http",
        forward_host="app",
        forward_port=3000,
        dry_run=True,
    )
    assert preview["dry_run"] is True
    assert [(step["method"], step["path"]) for step in preview["steps"]] == [
        ("POST", "/nginx/certificates"),
        ("POST", "/nginx/proxy-hosts"),
    ]
    assert all("json" in step for step in preview["steps"])
    assert preview["steps"][1]["json"]["certificate_id"] == "<created certificate id>"
    assert preview["steps"][1]["json"]["forward_port"] == 3000
    # Only the unauthenticated version probe; nothing is created.
    assert [(c.request.method, c.request.url.path) for c in mock.calls] == [("GET", "/api/")]
    print(json.dumps(preview, indent=2))
    print("\nHTTP calls: 1 (GET /api/ version check). Preview only; no certificate or host created.")
