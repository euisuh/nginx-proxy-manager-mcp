from unittest.mock import MagicMock
import pytest
from nginx_proxy_manager_mcp.tools.streams import StreamTools


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def tools(client):
    return StreamTools(client)


def test_list_streams(tools, client):
    client.get.return_value = [{"id": 1, "incoming_port": 2222}]
    assert tools.list_streams() == [{"id": 1, "incoming_port": 2222}]
    client.get.assert_called_once_with("/nginx/streams")


def test_get_stream(tools, client):
    client.get.return_value = {"id": 2, "incoming_port": 5432}
    assert tools.get_stream(2)["id"] == 2
    client.get.assert_called_once_with("/nginx/streams/2")


def test_create_stream(tools, client):
    client.post.return_value = {"id": 3}
    tools.create_stream(
        incoming_port=2222,
        forwarding_host="192.168.1.20",
        forwarding_port=22,
    )
    payload = client.post.call_args.kwargs["json"]
    assert payload["incoming_port"] == 2222
    assert payload["forwarding_host"] == "192.168.1.20"
    assert payload["forwarding_port"] == 22
    assert payload["tcp_forwarding"] is True
    assert payload["udp_forwarding"] is False


def test_create_stream_dry_run_does_not_post(tools, client):
    result = tools.create_stream(
        incoming_port=2222,
        forwarding_host="192.168.1.20",
        forwarding_port=22,
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["path"] == "/nginx/streams"
    assert result["json"]["incoming_port"] == 2222
    client.post.assert_not_called()


def test_update_stream_merges(tools, client):
    client.get.return_value = {"id": 1, "incoming_port": 2222, "forwarding_port": 22}
    client.put.return_value = {"id": 1, "forwarding_port": 2223}
    tools.update_stream(1, forwarding_port=2223)
    payload = client.put.call_args.kwargs["json"]
    assert payload["incoming_port"] == 2222
    assert payload["forwarding_port"] == 2223
    client.get.assert_called_once_with("/nginx/streams/1")


def test_update_stream_dry_run_merges_without_put(tools, client):
    client.get.return_value = {"id": 1, "incoming_port": 2222, "forwarding_port": 22}
    result = tools.update_stream(1, forwarding_port=2223, dry_run=True)
    assert result["path"] == "/nginx/streams/1"
    assert result["json"]["forwarding_port"] == 2223
    client.put.assert_not_called()


def test_delete_stream(tools, client):
    client.delete.return_value = True
    tools.delete_stream(4)
    client.delete.assert_called_once_with("/nginx/streams/4")


def test_enable_stream(tools, client):
    client.post.return_value = {}
    tools.enable_stream(4)
    client.post.assert_called_once_with("/nginx/streams/4/enable")


def test_disable_stream(tools, client):
    client.post.return_value = {}
    tools.disable_stream(4)
    client.post.assert_called_once_with("/nginx/streams/4/disable")


@pytest.mark.parametrize(
    "kwargs, expected_ids",
    [
        ({}, [1, 2]),
        ({"compact": True}, [1, 2]),
        ({"enabled": True}, [1]),
        ({"enabled": False}, [2]),
        ({"compact": True, "enabled": True}, [1]),
    ],
)
def test_list_streams_filters(tools, client, kwargs, expected_ids):
    keys = [
        "id",
        "incoming_port",
        "forwarding_host",
        "forwarding_port",
        "tcp_forwarding",
        "udp_forwarding",
        "enabled",
    ]
    first = {key: f"value-{key}" for key in reversed(keys)}
    first.update(
        id=1, enabled=1, domain_names=["other.org", "App.Example.com"], extra={"nested": True}
    )
    second = {"id": 2, "enabled": 0, "domain_names": ["b.org"], "extra": 9}
    items = [first, second]
    client.get.return_value = items
    original = [dict(item) for item in items]

    result = tools.list_streams(**kwargs)

    assert [item["id"] for item in result] == expected_ids
    if kwargs.get("compact"):
        expected = [
            {key: item[key] for key in keys if key in item}
            for item in items
            if item["id"] in expected_ids
        ]
        assert result == expected
        for item in result:
            assert list(item) == [key for key in keys if key in item]
    else:
        assert result == [item for item in items if item["id"] in expected_ids]
    if not kwargs:
        assert result is items
    assert items == original
    client.get.assert_called_once_with("/nginx/streams")
