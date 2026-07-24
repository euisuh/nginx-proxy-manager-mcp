from unittest.mock import MagicMock
import pytest
from nginx_proxy_manager_mcp.tools.proxy_hosts import ProxyHostTools


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def tools(client):
    return ProxyHostTools(client)


def test_list_proxy_hosts(tools, client):
    client.get.return_value = [{"id": 1, "domain_names": ["example.com"]}]
    result = tools.list_proxy_hosts()
    assert result == [{"id": 1, "domain_names": ["example.com"]}]
    client.get.assert_called_once_with("/nginx/proxy-hosts")


def test_get_proxy_host(tools, client):
    client.get.return_value = {"id": 5, "domain_names": ["sub.example.com"]}
    result = tools.get_proxy_host(5)
    assert result["id"] == 5
    client.get.assert_called_once_with("/nginx/proxy-hosts/5")


def test_create_proxy_host(tools, client):
    client.post.return_value = {"id": 10}
    result = tools.create_proxy_host(
        domain_names=["new.example.com"],
        forward_scheme="http",
        forward_host="192.168.1.10",
        forward_port=3000,
    )
    assert result == {"id": 10}
    payload = client.post.call_args[1]["json"]
    assert payload["domain_names"] == ["new.example.com"]
    assert payload["forward_host"] == "192.168.1.10"
    assert payload["forward_port"] == 3000
    assert payload["block_exploits"] is True
    assert payload["advanced_config"] == ""
    assert payload["meta"] == {}
    assert payload["locations"] == []


def test_create_proxy_host_dry_run_does_not_post(tools, client):
    result = tools.create_proxy_host(
        domain_names=["new.example.com"],
        forward_scheme="http",
        forward_host="192.168.1.10",
        forward_port=3000,
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["path"] == "/nginx/proxy-hosts"
    assert result["json"]["domain_names"] == ["new.example.com"]
    client.post.assert_not_called()


def test_create_proxy_host_with_letsencrypt_success(tools, client):
    client.post.side_effect = [
        {"id": 5, "provider": "letsencrypt"},
        {"id": 10, "domain_names": ["new.example.com"]},
    ]
    result = tools.create_proxy_host_with_letsencrypt(
        domain_names=["new.example.com"],
        forward_scheme="http",
        forward_host="192.168.1.10",
        forward_port=3000,
        email="admin@example.com",
    )
    assert result["ok"] is True
    assert result["certificate"]["id"] == 5
    assert result["proxy_host"]["id"] == 10
    cert_call, proxy_call = client.post.call_args_list
    assert cert_call.args == ("/nginx/certificates",)
    assert cert_call.kwargs["json"]["meta"]["letsencrypt_email"] == "admin@example.com"
    assert proxy_call.args == ("/nginx/proxy-hosts",)
    assert proxy_call.kwargs["json"]["certificate_id"] == 5
    assert proxy_call.kwargs["json"]["ssl_forced"] is True


def test_create_proxy_host_with_letsencrypt_dry_run_does_not_post(tools, client):
    result = tools.create_proxy_host_with_letsencrypt(
        domain_names=["new.example.com"],
        forward_scheme="http",
        forward_host="192.168.1.10",
        forward_port=3000,
        email="admin@example.com",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["steps"][0]["path"] == "/nginx/certificates"
    assert result["steps"][1]["path"] == "/nginx/proxy-hosts"
    assert result["steps"][1]["json"]["ssl_forced"] is True
    client.post.assert_not_called()


def test_create_proxy_host_with_letsencrypt_returns_created_cert_on_proxy_failure(tools, client):
    client.post.side_effect = [
        {"id": 5, "provider": "letsencrypt"},
        RuntimeError("proxy failed"),
    ]
    result = tools.create_proxy_host_with_letsencrypt(
        domain_names=["new.example.com"],
        forward_scheme="http",
        forward_host="192.168.1.10",
        forward_port=3000,
        email="admin@example.com",
    )
    assert result["ok"] is False
    assert result["failed_step"] == "create_proxy_host"
    assert result["created_certificate"]["id"] == 5
    assert result["created_proxy_host"] is None


def test_update_proxy_host_merges_fields(tools, client):
    client.get.return_value = {
        "id": 1,
        "domain_names": ["old.example.com"],
        "forward_host": "192.168.1.1",
        "forward_port": 80,
        "forward_scheme": "http",
    }
    client.put.return_value = {"id": 1, "forward_port": 443}
    result = tools.update_proxy_host(1, forward_port=443)
    assert result == {"id": 1, "forward_port": 443}
    put_payload = client.put.call_args[1]["json"]
    assert put_payload["forward_port"] == 443
    assert put_payload["domain_names"] == ["old.example.com"]
    client.get.assert_called_once_with("/nginx/proxy-hosts/1")


def test_update_proxy_host_dry_run_merges_without_put(tools, client):
    client.get.return_value = {
        "id": 1,
        "domain_names": ["old.example.com"],
        "forward_host": "192.168.1.1",
        "forward_port": 80,
        "forward_scheme": "http",
    }
    result = tools.update_proxy_host(1, forward_port=443, dry_run=True)
    assert result["dry_run"] is True
    assert result["method"] == "PUT"
    assert result["path"] == "/nginx/proxy-hosts/1"
    assert result["json"]["forward_port"] == 443
    assert result["json"]["domain_names"] == ["old.example.com"]
    client.get.assert_called_once_with("/nginx/proxy-hosts/1")
    client.put.assert_not_called()


def test_delete_proxy_host(tools, client):
    client.delete.return_value = True
    tools.delete_proxy_host(3)
    client.delete.assert_called_once_with("/nginx/proxy-hosts/3")


def test_delete_proxy_host_dry_run_does_not_delete(tools, client):
    result = tools.delete_proxy_host(3, dry_run=True)
    assert result == {"dry_run": True, "method": "DELETE", "path": "/nginx/proxy-hosts/3"}
    client.delete.assert_not_called()


def test_enable_proxy_host(tools, client):
    client.post.return_value = {}
    tools.enable_proxy_host(2)
    client.post.assert_called_once_with("/nginx/proxy-hosts/2/enable")


def test_enable_proxy_host_dry_run_does_not_post(tools, client):
    result = tools.enable_proxy_host(2, dry_run=True)
    assert result == {"dry_run": True, "method": "POST", "path": "/nginx/proxy-hosts/2/enable"}
    client.post.assert_not_called()


def test_disable_proxy_host(tools, client):
    client.post.return_value = {}
    tools.disable_proxy_host(2)
    client.post.assert_called_once_with("/nginx/proxy-hosts/2/disable")


def test_disable_proxy_host_dry_run_does_not_post(tools, client):
    result = tools.disable_proxy_host(2, dry_run=True)
    assert result == {"dry_run": True, "method": "POST", "path": "/nginx/proxy-hosts/2/disable"}
    client.post.assert_not_called()
