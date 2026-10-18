import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest
from fastmcp import FastMCP

from nginx_proxy_manager_mcp.server import register_all
from nginx_proxy_manager_mcp.tools.diagnose import DiagnoseTools, register_diagnose_tools


@pytest.fixture
def data():
    return {
        "/nginx/proxy-hosts": [
            {"id": 1, "domain_names": ["app.example.com"], "forward_scheme": "http",
             "forward_host": "app", "forward_port": 3000, "enabled": 1,
             "certificate_id": 10, "meta": {"private": True}},
            {"id": 2, "domain_names": ["*.example.com"], "certificate_id": 99},
            {"id": 3, "domain_names": ["no-cert.example.org"], "certificate_id": 0},
        ],
        "/nginx/redirection-hosts": [
            {"id": 4, "domain_names": ["APP.EXAMPLE.COM"], "forward_scheme": "https",
             "forward_domain_name": "example.org", "forward_http_code": 301,
             "enabled": 0, "certificate_id": 10, "meta": {"private": True}},
        ],
        "/nginx/certificates": [
            {"id": 10, "domain_names": ["*.example.com"], "provider": "letsencrypt",
             "expires_on": "2026-10-25 00:00:00"},
            {"id": 11, "domain_names": ["other.org"], "provider": "other",
             "expires_on": "2027-03-01T00:00:00Z"},
            {"id": 12, "domain_names": ["old.org"], "provider": "letsencrypt",
             "expires_on": "2026-10-10T00:00:00Z"},
        ],
    }


@pytest.fixture
def client(data):
    client = MagicMock()
    client.get.side_effect = data.__getitem__
    return client


@pytest.fixture
def tools(client, monkeypatch):
    monkeypatch.setattr(
        "nginx_proxy_manager_mcp.tools.diagnose._now",
        lambda: datetime(2026, 10, 18, tzinfo=timezone.utc),
    )
    return DiagnoseTools(client)


@pytest.mark.parametrize("domain", ["app.example.com", "APP.Example.COM"])
def test_find_exact_case_and_wildcard(tools, client, data, domain):
    result = tools.find_host_by_domain(domain)
    assert result == {
        "proxy_hosts": [
            {"id": 1, "domain_names": ["app.example.com"], "forward_scheme": "http",
             "forward_host": "app", "forward_port": 3000, "enabled": 1,
             "certificate_id": 10,
             "certificate": {"id": 10, "provider": "letsencrypt", "expires_on": "2026-10-25 00:00:00"}},
            {"id": 2, "domain_names": ["*.example.com"], "certificate_id": 99, "certificate": None},
        ],
        "redirection_hosts": [
            {"id": 4, "domain_names": ["APP.EXAMPLE.COM"], "forward_scheme": "https",
             "forward_domain_name": "example.org", "forward_http_code": 301,
             "enabled": 0, "certificate_id": 10,
             "certificate": {"id": 10, "provider": "letsencrypt", "expires_on": "2026-10-25 00:00:00"}},
        ],
        "certificates": [data["/nginx/certificates"][0]],
    }
    assert client.mock_calls == [call.get(path) for path in data]


@pytest.mark.parametrize("domain", ["example.com", "absent.org", "badexample.com"])
def test_find_no_match_or_wildcard_apex(tools, domain):
    assert tools.find_host_by_domain(domain) == {
        "proxy_hosts": [], "redirection_hosts": [], "certificates": [],
    }


def test_find_without_certificate(tools):
    result = tools.find_host_by_domain("no-cert.example.org")
    assert result["proxy_hosts"][0]["certificate"] is None


@pytest.mark.parametrize("domain", ["https://example.com", "a.*.example.com", ""])
def test_find_validates_domain_before_fetch(tools, client, domain):
    with pytest.raises(ValueError):
        tools.find_host_by_domain(domain)
    client.get.assert_not_called()


def test_expiry_window_sorted_expired_and_used_by(tools, client, data):
    assert tools.list_expiring_certificates() == [
        {**data["/nginx/certificates"][2], "days_left": -8, "used_by": []},
        {**data["/nginx/certificates"][0], "days_left": 7,
         "used_by": [{"type": "proxy_host", "id": 1}, {"type": "redirection_host", "id": 4}]},
    ]
    assert client.mock_calls == [call.get(path) for path in data]


@pytest.mark.parametrize("expiry", [
    "2026-11-17 00:00:00", "2026-11-17T00:00:00Z", "2026-11-17T02:00:00+02:00",
])
def test_expiry_boundary_and_formats(tools, data, expiry):
    data["/nginx/certificates"] = [
        {"id": 20, "expires_on": expiry},
        {"id": 21, "expires_on": "2026-11-17T00:00:01Z"},
    ]
    result = tools.list_expiring_certificates(30)
    assert [cert["id"] for cert in result] == [20]
    assert result[0]["days_left"] == 30


def test_expiry_missing_dates_and_empty_data(tools, data):
    data["/nginx/certificates"] = [{"id": 20}, {"id": 21, "expires_on": None}]
    assert tools.list_expiring_certificates() == []
    for path in data:
        data[path] = []
    assert tools.list_expiring_certificates() == []


@pytest.mark.parametrize("days", [1, 3650])
def test_valid_days_limits(tools, days):
    assert tools.list_expiring_certificates(days)[0]["days_left"] == -8


@pytest.mark.parametrize("days", [0, -1, 3651, True, 1.5, "30", None])
def test_bad_days_before_fetch(tools, client, days):
    with pytest.raises(ValueError, match="days"):
        tools.list_expiring_certificates(days)
    client.get.assert_not_called()


@pytest.mark.parametrize("read_only", [False, True])
@pytest.mark.parametrize("register", [register_diagnose_tools, register_all])
def test_diagnose_registration(register, read_only):
    mcp = FastMCP("diagnose-test")
    register(mcp, object(), read_only=read_only)
    names = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert {"find_host_by_domain", "list_expiring_certificates"} <= names


def test_wildcard_matches_one_label_only():
    from nginx_proxy_manager_mcp.tools.diagnose import _matches

    assert _matches("a.example.com", ["*.example.com"])
    assert not _matches("a.b.example.com", ["*.example.com"])
    assert not _matches("example.com", ["*.example.com"])
