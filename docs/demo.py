"""Record the real HTTPS workflow preview with all HTTP calls mocked."""

import json
import os
from unittest.mock import patch

import respx

from nginx_proxy_manager_mcp.npm_client import NPMClient
from nginx_proxy_manager_mcp.tools.proxy_hosts import ProxyHostTools


with patch.dict(os.environ, {
    "NPM_URL": "http://npm.test",
    "NPM_EMAIL": "demo@example.com",
    "NPM_PASSWORD": "mock-only",
}), respx.mock(assert_all_mocked=True) as mock, NPMClient() as client:
    tools = ProxyHostTools(client)
    print("Mocked NPM API; no real credentials or network requests.\n")
    print('create_proxy_host_with_letsencrypt(')
    print('    domain_names=["blog.example.com"], forward_scheme="http",')
    print('    forward_host="app", forward_port=3000,')
    print('    email="demo@example.com", dry_run=True)\n')
    preview = tools.create_proxy_host_with_letsencrypt(
        domain_names=["blog.example.com"],
        forward_scheme="http",
        forward_host="app",
        forward_port=3000,
        email="demo@example.com",
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
    assert mock.calls.call_count == 0
    print(json.dumps(preview, indent=2))
    print("\nHTTP calls: 0. Preview only; no certificate or host created.")
