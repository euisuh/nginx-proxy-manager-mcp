from unittest.mock import MagicMock
import pytest
from tools.ssl_certs import SSLCertTools


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


def test_renew_certificate(tools, client):
    client.post.return_value = {"id": 5}
    tools.renew_certificate(5)
    client.post.assert_called_once_with("/nginx/certificates/5/renew")
