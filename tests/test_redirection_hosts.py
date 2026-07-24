from unittest.mock import MagicMock
import pytest
from nginx_proxy_manager_mcp.tools.redirection_hosts import RedirectionHostTools


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def tools(client):
    return RedirectionHostTools(client)


def test_list_redirection_hosts(tools, client):
    client.get.return_value = [{"id": 1, "domain_names": ["old.example.com"]}]
    assert tools.list_redirection_hosts() == [{"id": 1, "domain_names": ["old.example.com"]}]
    client.get.assert_called_once_with("/nginx/redirection-hosts")


def test_get_redirection_host(tools, client):
    client.get.return_value = {"id": 2, "domain_names": ["go.example.com"]}
    assert tools.get_redirection_host(2)["id"] == 2
    client.get.assert_called_once_with("/nginx/redirection-hosts/2")


def test_create_redirection_host(tools, client):
    client.post.return_value = {"id": 3}
    tools.create_redirection_host(
        domain_names=["go.example.com"],
        forward_domain_name="target.example.com",
        forward_http_code=301,
    )
    payload = client.post.call_args.kwargs["json"]
    assert payload["domain_names"] == ["go.example.com"]
    assert payload["forward_domain_name"] == "target.example.com"
    assert payload["forward_http_code"] == 301
    assert payload["preserve_path"] is True
    assert payload["certificate_id"] == 0


def test_create_redirection_host_dry_run_does_not_post(tools, client):
    result = tools.create_redirection_host(
        domain_names=["go.example.com"],
        forward_domain_name="target.example.com",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["path"] == "/nginx/redirection-hosts"
    assert result["json"]["forward_domain_name"] == "target.example.com"
    client.post.assert_not_called()


def test_update_redirection_host_merges(tools, client):
    client.get.return_value = {"id": 1, "forward_http_code": 302, "preserve_path": True}
    client.put.return_value = {"id": 1, "forward_http_code": 301}
    tools.update_redirection_host(1, forward_http_code=301)
    payload = client.put.call_args.kwargs["json"]
    assert payload["forward_http_code"] == 301
    assert payload["preserve_path"] is True
    client.get.assert_called_once_with("/nginx/redirection-hosts/1")


def test_update_redirection_host_dry_run_merges_without_put(tools, client):
    client.get.return_value = {"id": 1, "forward_http_code": 302, "preserve_path": True}
    result = tools.update_redirection_host(1, forward_http_code=301, dry_run=True)
    assert result["path"] == "/nginx/redirection-hosts/1"
    assert result["json"]["forward_http_code"] == 301
    client.put.assert_not_called()


def test_delete_redirection_host(tools, client):
    client.delete.return_value = True
    tools.delete_redirection_host(4)
    client.delete.assert_called_once_with("/nginx/redirection-hosts/4")


def test_enable_redirection_host(tools, client):
    client.post.return_value = {}
    tools.enable_redirection_host(4)
    client.post.assert_called_once_with("/nginx/redirection-hosts/4/enable")


def test_disable_redirection_host(tools, client):
    client.post.return_value = {}
    tools.disable_redirection_host(4)
    client.post.assert_called_once_with("/nginx/redirection-hosts/4/disable")
