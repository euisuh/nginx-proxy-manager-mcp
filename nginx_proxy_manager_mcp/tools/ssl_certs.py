from __future__ import annotations
from typing import Annotated, TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from nginx_proxy_manager_mcp.npm_client import NPMClient

from nginx_proxy_manager_mcp.tools.previews import dry_run_preview
from nginx_proxy_manager_mcp.validation import validate_domain_names, validate_email, validate_positive_id


class SSLCertTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_certificates(self) -> list[dict]:
        """List SSL certificates known to NPM, including expiry information when provided by NPM. Use this to inspect available certificates; create_letsencrypt_cert requests a new certificate and renew_certificate renews an existing one. This is read-only and makes no certificate request. Returns certificate objects with IDs, domains, provider, and expiry fields."""
        return self.client.get("/nginx/certificates")

    def create_letsencrypt_cert(
        self,
        domain_names: Annotated[list[str], Field(description="Domain names routed by this host or certificate.")],
        email: Annotated[str, Field(description="Email address supplied to Let's Encrypt for certificate requests.")],
        dns_challenge: Annotated[bool, Field(description="Use DNS validation instead of HTTP validation for the certificate request.")] = False,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Request a new Let's Encrypt certificate for the supplied domains. Use this when a certificate is needed without creating a proxy host; create_proxy_host_with_letsencrypt also creates an HTTPS-forced host. This sends a certificate request to NPM and may contact Let's Encrypt. Returns the certificate object with its ID, domains, and status. Set dry_run=True to preview the exact request without changing NPM."""
        validate_domain_names(domain_names)
        validate_email(email)
        payload = {
            "provider": "letsencrypt",
            "domain_names": domain_names,
            "meta": {
                "letsencrypt_email": email,
                "letsencrypt_agree": True,
                "dns_challenge": dns_challenge,
            },
        }
        if dry_run:
            return dry_run_preview("POST", "/nginx/certificates", payload)
        return self.client.post("/nginx/certificates", json=payload)

    def renew_certificate(self, id: Annotated[int, Field(description="ID of the certificate to renew, from list_certificates.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Request renewal of an existing certificate by ID. Use this for a certificate already managed by NPM; use create_letsencrypt_cert to request a new certificate. This triggers NPM certificate renewal processing and may contact the certificate provider. Returns the certificate operation result, including available certificate fields. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/certificates/{id}/renew")
        return self.client.post(f"/nginx/certificates/{id}/renew")


def register_ssl_cert_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = SSLCertTools(client)
    mcp.tool()(tools.list_certificates)
    mcp.tool()(tools.create_letsencrypt_cert)
    mcp.tool()(tools.renew_certificate)
