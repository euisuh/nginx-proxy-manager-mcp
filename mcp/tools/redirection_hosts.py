from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from npm_client import NPMClient

from tools.previews import dry_run_preview
from validation import (
    validate_domain_names,
    validate_forward_scheme,
    validate_host,
    validate_optional_positive_id,
    validate_positive_id,
    validate_redirect_code,
)


class RedirectionHostTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_redirection_hosts(self) -> list[dict]:
        """List all redirection hosts with their current status."""
        return self.client.get("/nginx/redirection-hosts")

    def get_redirection_host(self, id: int) -> dict:
        """Get a single redirection host by ID."""
        validate_positive_id(id)
        return self.client.get(f"/nginx/redirection-hosts/{id}")

    def create_redirection_host(
        self,
        domain_names: list[str],
        forward_domain_name: str,
        forward_http_code: int = 302,
        forward_scheme: str = "https",
        preserve_path: bool = True,
        ssl_forced: bool = False,
        certificate_id: Optional[int] = None,
        block_exploits: bool = True,
        dry_run: bool = False,
    ) -> dict:
        """Create a redirection host. Set dry_run=True to preview without changing NPM."""
        validate_domain_names(domain_names)
        validate_host(forward_domain_name, "forward_domain_name")
        validate_redirect_code(forward_http_code)
        validate_forward_scheme(forward_scheme)
        validate_optional_positive_id(certificate_id, "certificate_id")
        payload = {
            "domain_names": domain_names,
            "forward_domain_name": forward_domain_name,
            "forward_http_code": forward_http_code,
            "forward_scheme": forward_scheme,
            "preserve_path": preserve_path,
            "ssl_forced": ssl_forced,
            "certificate_id": certificate_id or 0,
            "block_exploits": block_exploits,
            "advanced_config": "",
            "meta": {},
        }
        if dry_run:
            return dry_run_preview("POST", "/nginx/redirection-hosts", payload)
        return self.client.post("/nginx/redirection-hosts", json=payload)

    def update_redirection_host(
        self,
        id: int,
        domain_names: Optional[list[str]] = None,
        forward_domain_name: Optional[str] = None,
        forward_http_code: Optional[int] = None,
        forward_scheme: Optional[str] = None,
        preserve_path: Optional[bool] = None,
        ssl_forced: Optional[bool] = None,
        certificate_id: Optional[int] = None,
        block_exploits: Optional[bool] = None,
        dry_run: bool = False,
    ) -> dict:
        """Update a redirection host. Set dry_run=True to preview the merged payload."""
        validate_positive_id(id)
        if domain_names is not None:
            validate_domain_names(domain_names)
        if forward_domain_name is not None:
            validate_host(forward_domain_name, "forward_domain_name")
        if forward_http_code is not None:
            validate_redirect_code(forward_http_code)
        if forward_scheme is not None:
            validate_forward_scheme(forward_scheme)
        validate_optional_positive_id(certificate_id, "certificate_id")
        existing = self.client.get(f"/nginx/redirection-hosts/{id}")
        updates = {
            k: v
            for k, v in {
                "domain_names": domain_names,
                "forward_domain_name": forward_domain_name,
                "forward_http_code": forward_http_code,
                "forward_scheme": forward_scheme,
                "preserve_path": preserve_path,
                "ssl_forced": ssl_forced,
                "certificate_id": certificate_id,
                "block_exploits": block_exploits,
            }.items()
            if v is not None
        }
        existing.update(updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/redirection-hosts/{id}", existing)
        return self.client.put(f"/nginx/redirection-hosts/{id}", json=existing)

    def delete_redirection_host(self, id: int, dry_run: bool = False) -> bool | dict:
        """Delete a redirection host. Set dry_run=True to preview only."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/redirection-hosts/{id}")
        return self.client.delete(f"/nginx/redirection-hosts/{id}")

    def enable_redirection_host(self, id: int, dry_run: bool = False) -> dict:
        """Enable a redirection host. Set dry_run=True to preview only."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/redirection-hosts/{id}/enable")
        return self.client.post(f"/nginx/redirection-hosts/{id}/enable")

    def disable_redirection_host(self, id: int, dry_run: bool = False) -> dict:
        """Disable a redirection host. Set dry_run=True to preview only."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/redirection-hosts/{id}/disable")
        return self.client.post(f"/nginx/redirection-hosts/{id}/disable")


def register_redirection_host_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = RedirectionHostTools(client)
    mcp.tool()(tools.list_redirection_hosts)
    mcp.tool()(tools.get_redirection_host)
    mcp.tool()(tools.create_redirection_host)
    mcp.tool()(tools.update_redirection_host)
    mcp.tool()(tools.delete_redirection_host)
    mcp.tool()(tools.enable_redirection_host)
    mcp.tool()(tools.disable_redirection_host)
