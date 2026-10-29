from __future__ import annotations
from typing import Annotated, Optional, TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from nginx_proxy_manager_mcp.npm_client import NPMClient

from nginx_proxy_manager_mcp.tools import register_tools
from nginx_proxy_manager_mcp.tools.filters import filter_items
from nginx_proxy_manager_mcp.tools.payloads import letsencrypt_payload, redact_certificate_payload
from nginx_proxy_manager_mcp.tools.previews import dry_run_preview
from nginx_proxy_manager_mcp.validation import validate_domain_names, validate_email, validate_positive_id


class SSLCertTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_certificates(
        self,
        domain: Annotated[Optional[str], Field(description="Case-insensitive substring to match against any domain name; omit for all domains.")] = None,
        compact: Annotated[bool, Field(description="Return only summary fields when True; defaults to full NPM objects.")] = False,
    ) -> list[dict]:
        """List SSL certificates known to NPM, including expiry information when provided by NPM. Use this to inspect available certificates; create_letsencrypt_cert requests a new certificate and renew_certificate renews an existing one. This is read-only and makes no certificate request. Filter domain names by a case-insensitive substring with domain. Set compact=True to return only summary fields. Returns certificate objects with IDs, domains, provider, and expiry fields."""
        return filter_items(
            self.client.get("/nginx/certificates"),
            domain=domain,
            compact=compact,
            compact_keys=(
                "id",
                "provider",
                "domain_names",
                "expires_on",
            ),
        )

    def create_letsencrypt_cert(
        self,
        domain_names: Annotated[list[str], Field(description="Domain names routed by this host or certificate.")],
        email: Annotated[Optional[str], Field(description="Let's Encrypt account email. Required on NPM before 2.13; ignored on 2.13+, where NPM uses the NPM user's account email.")] = None,
        dns_challenge: Annotated[bool, Field(description="Use DNS-01 validation instead of HTTP-01. Required for wildcard domains; needs dns_provider and dns_provider_credentials.")] = False,
        dns_provider: Annotated[Optional[str], Field(description="Certbot DNS plugin ID known to NPM, for example cloudflare, route53 or digitalocean. Only with dns_challenge=True.")] = None,
        dns_provider_credentials: Annotated[Optional[str], Field(description="Credentials file contents for the DNS plugin, for example 'dns_cloudflare_api_token = ...'. Only with dns_challenge=True. NPM never returns it; dry-run previews redact it.")] = None,
        propagation_seconds: Annotated[Optional[int], Field(description="Seconds to wait for DNS propagation before validation; omit for the plugin default. Only with dns_challenge=True.")] = None,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Request a new Let's Encrypt certificate for the supplied domains, over HTTP-01 by default or DNS-01 with dns_challenge=True (required for wildcards). Use this when a certificate is needed without creating a proxy host; create_proxy_host_with_letsencrypt also creates an HTTPS-forced host. This sends a certificate request to NPM and may contact Let's Encrypt. Returns the certificate object with its ID, domains, and status. Set dry_run=True to preview the exact request without changing NPM."""
        validate_domain_names(domain_names)
        if email is not None:
            validate_email(email)
        payload = letsencrypt_payload(
            self.client, domain_names, email, dns_challenge,
            dns_provider, dns_provider_credentials, propagation_seconds,
        )
        if dry_run:
            return dry_run_preview("POST", "/nginx/certificates", redact_certificate_payload(payload))
        return self.client.post("/nginx/certificates", json=payload)

    def get_certificate(self, id: Annotated[int, Field(description="ID of the certificate, from list_certificates.")]) -> dict:
        """Fetch one certificate by ID, including provider, domain names, expiry and meta. Use this for one certificate's details; use list_certificates to find IDs and find_host_by_domain to see which hosts use it. This is read-only; NPM never returns DNS provider credentials or private keys. Returns the NPM certificate object."""
        validate_positive_id(id)
        return self.client.get(f"/nginx/certificates/{id}")

    def delete_certificate(self, id: Annotated[int, Field(description="ID of the certificate to delete, from list_certificates.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> bool | dict:
        """Permanently delete a certificate by ID, for example one left behind when create_proxy_host_with_letsencrypt fails at the proxy step. NPM also revokes Let's Encrypt certificates on delete and does not detach hosts that use it, so check find_host_by_domain first and detach with update_proxy_host(certificate_id=0). Deletion cannot be undone. Returns True on success. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/certificates/{id}")
        return self.client.delete(f"/nginx/certificates/{id}")

    def renew_certificate(self, id: Annotated[int, Field(description="ID of the certificate to renew, from list_certificates.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Request renewal of an existing certificate by ID. Use this for a certificate already managed by NPM; use create_letsencrypt_cert to request a new certificate. This triggers NPM certificate renewal processing and may contact the certificate provider. Returns the certificate operation result, including available certificate fields. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/certificates/{id}/renew")
        return self.client.post(f"/nginx/certificates/{id}/renew")


def register_ssl_cert_tools(mcp: FastMCP, client: NPMClient, *, read_only: bool = False) -> None:
    tools = SSLCertTools(client)
    register_tools(mcp, (
        tools.list_certificates,
        tools.get_certificate,
        tools.create_letsencrypt_cert,
        tools.delete_certificate,
        tools.renew_certificate,
    ), read_only)
