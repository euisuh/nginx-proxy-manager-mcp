"""Run the proxy-host tools against a real NPM container.

Skipped unless NPM_LIVE_URL is set (the `integration` CI job sets it).
"""
import os
import time

import httpx
import pytest

BASE = os.environ.get("NPM_LIVE_URL", "").rstrip("/")
EMAIL, PASSWORD = "integration@example.com", "integration-pass-1234"

pytestmark = pytest.mark.skipif(not BASE, reason="NPM_LIVE_URL not set")


def wait_for_api() -> dict:
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{BASE}/api/", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except httpx.HTTPError:
            pass
        time.sleep(3)
    raise TimeoutError(f"NPM did not answer at {BASE}/api/")


def create_admin() -> None:
    body = {
        "name": "Integration",
        "nickname": "integration",
        "email": EMAIL,
        "roles": ["admin"],
        "is_disabled": False,
        "auth": {"type": "password", "secret": PASSWORD},
    }
    resp = httpx.post(f"{BASE}/api/users", json=body, timeout=30)
    assert resp.status_code in (200, 201), f"admin setup failed: {resp.status_code} {resp.text}"


@pytest.fixture(scope="module")
def client():
    info = wait_for_api()
    if not info.get("setup"):
        create_admin()
    os.environ.update(NPM_URL=BASE, NPM_EMAIL=EMAIL, NPM_PASSWORD=PASSWORD)
    from nginx_proxy_manager_mcp.npm_client import NPMClient

    with NPMClient() as c:
        yield c


def test_version_probe(client):
    major, minor = client.npm_version()
    assert (major, minor) >= (2, 12)


def test_proxy_host_create_list_delete(client):
    from nginx_proxy_manager_mcp.tools.proxy_hosts import ProxyHostTools

    tools = ProxyHostTools(client)
    domain = "integration.example.test"
    created = tools.create_proxy_host(
        domain_names=[domain], forward_scheme="http", forward_host="127.0.0.1", forward_port=8080,
        dry_run=False,
    )
    host_id = created["id"]
    try:
        assert domain in [d for h in tools.list_proxy_hosts() for d in h["domain_names"]]
        assert tools.get_proxy_host(host_id)["forward_port"] == 8080
    finally:
        assert tools.delete_proxy_host(host_id, dry_run=False) is True
    assert host_id not in [h["id"] for h in tools.list_proxy_hosts()]
