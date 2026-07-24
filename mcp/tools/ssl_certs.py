from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from npm_client import NPMClient

from tools.previews import dry_run_preview


class SSLCertTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_certificates(self) -> list[dict]:
        """List all SSL certificates including expiry dates."""
        return self.client.get("/nginx/certificates")

    def create_letsencrypt_cert(
        self,
        domain_names: list[str],
        email: str,
        dns_challenge: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """Request a Let's Encrypt certificate. Set dry_run=True to preview only."""
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

    def renew_certificate(self, id: int, dry_run: bool = False) -> dict:
        """Trigger certificate renewal. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("POST", f"/nginx/certificates/{id}/renew")
        return self.client.post(f"/nginx/certificates/{id}/renew")


def register_ssl_cert_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = SSLCertTools(client)
    mcp.tool()(tools.list_certificates)
    mcp.tool()(tools.create_letsencrypt_cert)
    mcp.tool()(tools.renew_certificate)
