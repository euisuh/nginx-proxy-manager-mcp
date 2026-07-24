from unittest.mock import MagicMock
import pytest
from nginx_proxy_manager_mcp.tools.access_lists import AccessListTools


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def tools(client):
    return AccessListTools(client)


def test_list_access_lists(tools, client):
    client.get.return_value = [{"id": 1, "name": "Private"}]
    result = tools.list_access_lists()
    assert result == [{"id": 1, "name": "Private"}]
    client.get.assert_called_once_with("/nginx/access-lists")


def test_get_access_list(tools, client):
    client.get.return_value = {"id": 2, "name": "Admins", "clients": [], "items": []}
    result = tools.get_access_list(2)
    assert result["name"] == "Admins"
    client.get.assert_called_once_with("/nginx/access-lists/2")


def test_create_access_list_defaults(tools, client):
    client.post.return_value = {"id": 3, "name": "New List"}
    tools.create_access_list(name="New List")
    payload = client.post.call_args[1]["json"]
    assert payload["name"] == "New List"
    assert payload["clients"] == []
    assert payload["items"] == []
    assert payload["satisfy_any"] is False


def test_create_access_list_with_ip(tools, client):
    client.post.return_value = {"id": 4}
    tools.create_access_list(
        name="Office Only",
        clients=[{"address": "203.0.113.0/24", "directive": "allow"}],
    )
    payload = client.post.call_args[1]["json"]
    assert payload["clients"] == [{"address": "203.0.113.0/24", "directive": "allow"}]


def test_create_access_list_dry_run_does_not_post(tools, client):
    result = tools.create_access_list(
        name="Office Only",
        clients=[{"address": "203.0.113.0/24", "directive": "allow"}],
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["path"] == "/nginx/access-lists"
    assert result["json"]["name"] == "Office Only"
    assert result["json"]["clients"] == [{"address": "203.0.113.0/24", "directive": "allow"}]
    client.post.assert_not_called()


def test_update_access_list_merges(tools, client):
    client.get.return_value = {"id": 1, "name": "Old", "satisfy_any": False, "pass_auth": False, "clients": [], "items": []}
    client.put.return_value = {"id": 1, "name": "New"}
    tools.update_access_list(1, name="New")
    put_payload = client.put.call_args[1]["json"]
    assert put_payload["name"] == "New"
    assert put_payload["satisfy_any"] is False
    client.get.assert_called_once_with("/nginx/access-lists/1")


def test_update_access_list_dry_run_merges_without_put(tools, client):
    client.get.return_value = {"id": 1, "name": "Old", "satisfy_any": False, "pass_auth": False, "clients": [], "items": []}
    result = tools.update_access_list(1, name="New", dry_run=True)
    assert result["dry_run"] is True
    assert result["method"] == "PUT"
    assert result["path"] == "/nginx/access-lists/1"
    assert result["json"]["name"] == "New"
    assert result["json"]["satisfy_any"] is False
    client.get.assert_called_once_with("/nginx/access-lists/1")
    client.put.assert_not_called()


def test_delete_access_list(tools, client):
    client.delete.return_value = True
    tools.delete_access_list(7)
    client.delete.assert_called_once_with("/nginx/access-lists/7")


def test_delete_access_list_dry_run_does_not_delete(tools, client):
    result = tools.delete_access_list(7, dry_run=True)
    assert result == {"dry_run": True, "method": "DELETE", "path": "/nginx/access-lists/7"}
    client.delete.assert_not_called()
