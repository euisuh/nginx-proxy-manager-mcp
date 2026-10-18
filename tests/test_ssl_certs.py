from unittest.mock import MagicMock
import pytest
from nginx_proxy_manager_mcp.tools.ssl_certs import SSLCertTools


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def tools(client):
    return SSLCertTools(client)


def test_list_certificates(tools, client):
    client.get.return_value = [{"id": 1, "domain_names": ["example.com"], "expires_on": "2026-12-01"}]
    result = tools.list_certificates()
    assert len(result) == 1
    client.get.assert_called_once_with("/nginx/certificates")


def test_create_letsencrypt_cert(tools, client):
    client.post.return_value = {"id": 5, "provider": "letsencrypt"}
    result = tools.create_letsencrypt_cert(
        domain_names=["example.com", "www.example.com"],
        email="admin@example.com",
    )
    assert result["provider"] == "letsencrypt"
    payload = client.post.call_args[1]["json"]
    assert payload["provider"] == "letsencrypt"
    assert payload["domain_names"] == ["example.com", "www.example.com"]
    assert payload["meta"]["letsencrypt_email"] == "admin@example.com"
    assert payload["meta"]["letsencrypt_agree"] is True


def test_create_letsencrypt_cert_dry_run_does_not_post(tools, client):
    result = tools.create_letsencrypt_cert(
        domain_names=["example.com", "www.example.com"],
        email="admin@example.com",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["path"] == "/nginx/certificates"
    assert result["json"]["domain_names"] == ["example.com", "www.example.com"]
    assert result["json"]["meta"]["letsencrypt_email"] == "admin@example.com"
    client.post.assert_not_called()


def test_renew_certificate(tools, client):
    client.post.return_value = {"id": 5}
    tools.renew_certificate(5)
    client.post.assert_called_once_with("/nginx/certificates/5/renew")


def test_renew_certificate_dry_run_does_not_post(tools, client):
    result = tools.renew_certificate(5, dry_run=True)
    assert result == {"dry_run": True, "method": "POST", "path": "/nginx/certificates/5/renew"}
    client.post.assert_not_called()


@pytest.mark.parametrize(
    "kwargs, expected_ids",
    [
        ({}, [1, 2]),
        ({"compact": True}, [1, 2]),
        ({"domain": "EXAMPLE"}, [1]),
        ({"domain": "absent"}, []),
        ({"compact": True, "domain": "example"}, [1]),
    ],
)
def test_list_certificates_filters(tools, client, kwargs, expected_ids):
    keys = ["id", "provider", "domain_names", "expires_on"]
    first = {key: f"value-{key}" for key in reversed(keys)}
    first.update(
        id=1, enabled=1, domain_names=["other.org", "App.Example.com"], extra={"nested": True}
    )
    second = {"id": 2, "enabled": 0, "domain_names": ["b.org"], "extra": 9}
    items = [first, second]
    client.get.return_value = items
    original = [dict(item) for item in items]

    result = tools.list_certificates(**kwargs)

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
    client.get.assert_called_once_with("/nginx/certificates")
