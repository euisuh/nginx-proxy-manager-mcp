from unittest.mock import MagicMock
import pytest
from nginx_proxy_manager_mcp.tools.ssl_certs import SSLCertTools


@pytest.fixture
def client():
    c = MagicMock()
    c.npm_version.return_value = (2, 16)
    return c


@pytest.fixture
def tools(client):
    return SSLCertTools(client)


def test_list_certificates(tools, client):
    client.get.return_value = [{"id": 1, "domain_names": ["example.com"], "expires_on": "2026-12-01"}]
    result = tools.list_certificates()
    assert len(result) == 1
    client.get.assert_called_once_with("/nginx/certificates")


def test_create_letsencrypt_cert_legacy_npm_sends_email(tools, client):
    client.npm_version.return_value = (2, 12)
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
    client.npm_version.return_value = (2, 12)
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


def test_create_letsencrypt_cert_npm_2_13_omits_removed_meta_fields(tools, client):
    # NPM >= 2.13 rejects letsencrypt_email/letsencrypt_agree (additionalProperties: false).
    client.post.return_value = {"id": 6}
    tools.create_letsencrypt_cert(domain_names=["example.com"], email="admin@example.com")
    payload = client.post.call_args[1]["json"]
    assert payload == {
        "provider": "letsencrypt",
        "domain_names": ["example.com"],
        "meta": {"dns_challenge": False},
    }


def test_create_letsencrypt_cert_email_optional_on_npm_2_13(tools, client):
    client.post.return_value = {"id": 6}
    tools.create_letsencrypt_cert(domain_names=["example.com"])
    assert "letsencrypt_email" not in client.post.call_args[1]["json"]["meta"]


def test_create_letsencrypt_cert_legacy_npm_requires_email(tools, client):
    client.npm_version.return_value = (2, 12)
    with pytest.raises(ValueError, match="email is required"):
        tools.create_letsencrypt_cert(domain_names=["example.com"])
    client.post.assert_not_called()


def test_create_letsencrypt_cert_rejects_bad_email(tools, client):
    with pytest.raises(ValueError, match="email"):
        tools.create_letsencrypt_cert(domain_names=["example.com"], email="not-an-email")
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


def test_get_certificate(tools, client):
    client.get.return_value = {"id": 5, "provider": "letsencrypt"}
    assert tools.get_certificate(5)["id"] == 5
    client.get.assert_called_once_with("/nginx/certificates/5")


def test_delete_certificate(tools, client):
    client.delete.return_value = True
    assert tools.delete_certificate(5) is True
    client.delete.assert_called_once_with("/nginx/certificates/5")


def test_delete_certificate_dry_run_does_not_delete(tools, client):
    result = tools.delete_certificate(5, dry_run=True)
    assert result == {"dry_run": True, "method": "DELETE", "path": "/nginx/certificates/5"}
    client.delete.assert_not_called()


def test_get_and_delete_certificate_reject_bad_id(tools, client):
    with pytest.raises(ValueError):
        tools.get_certificate(0)
    with pytest.raises(ValueError):
        tools.delete_certificate(-3)
    client.get.assert_not_called()
    client.delete.assert_not_called()


DNS_ARGS = {
    "dns_challenge": True,
    "dns_provider": "cloudflare",
    "dns_provider_credentials": "dns_cloudflare_api_token = s3cret",
}


def test_create_letsencrypt_cert_dns_challenge_wildcard(tools, client):
    client.post.return_value = {"id": 7}
    tools.create_letsencrypt_cert(
        domain_names=["*.example.com", "example.com"], propagation_seconds=60, **DNS_ARGS,
    )
    assert client.post.call_args[1]["json"]["meta"] == {
        "dns_challenge": True,
        "dns_provider": "cloudflare",
        "dns_provider_credentials": "dns_cloudflare_api_token = s3cret",
        "propagation_seconds": 60,
    }


def test_create_letsencrypt_cert_dns_dry_run_redacts_credentials(tools, client):
    result = tools.create_letsencrypt_cert(domain_names=["*.example.com"], dry_run=True, **DNS_ARGS)
    assert result["json"]["meta"]["dns_provider_credentials"] == "<redacted>"
    assert "s3cret" not in str(result)
    client.post.assert_not_called()


def test_create_letsencrypt_cert_dns_challenge_requires_provider_and_credentials(tools, client):
    with pytest.raises(ValueError, match="dns_provider"):
        tools.create_letsencrypt_cert(domain_names=["example.com"], dns_challenge=True)
    with pytest.raises(ValueError, match="dns_provider"):
        tools.create_letsencrypt_cert(
            domain_names=["example.com"], dns_challenge=True, dns_provider="cloudflare",
        )
    client.post.assert_not_called()


def test_create_letsencrypt_cert_dns_fields_need_dns_challenge(tools, client):
    with pytest.raises(ValueError, match="dns_challenge=True"):
        tools.create_letsencrypt_cert(domain_names=["example.com"], dns_provider="cloudflare")
    client.post.assert_not_called()


def test_create_letsencrypt_cert_rejects_negative_propagation(tools, client):
    with pytest.raises(ValueError, match="propagation_seconds"):
        tools.create_letsencrypt_cert(
            domain_names=["example.com"], propagation_seconds=-1, **DNS_ARGS,
        )


def test_create_letsencrypt_cert_wildcard_over_http_is_rejected(tools, client):
    with pytest.raises(ValueError, match="wildcard"):
        tools.create_letsencrypt_cert(domain_names=["*.example.com"])
    client.post.assert_not_called()
