from __future__ import annotations
from typing import Annotated, Optional, TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from nginx_proxy_manager_mcp.npm_client import NPMClient

from nginx_proxy_manager_mcp.tools import register_tools
from nginx_proxy_manager_mcp.tools.filters import filter_items
from nginx_proxy_manager_mcp.tools.payloads import update_payload
from nginx_proxy_manager_mcp.tools.previews import dry_run_preview
from nginx_proxy_manager_mcp.validation import (
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

    def list_redirection_hosts(
        self,
        domain: Annotated[Optional[str], Field(description="Case-insensitive substring to match against any domain name; omit for all domains.")] = None,
        enabled: Annotated[Optional[bool], Field(description="Keep items with this enabled status; omit for both enabled and disabled items.")] = None,
        compact: Annotated[bool, Field(description="Return only summary fields when True; defaults to full NPM objects.")] = False,
    ) -> list[dict]:
        """List configured redirection hosts and their current status. Use this to find IDs before fetching, changing, enabling, disabling, or deleting a redirect; proxy hosts handle upstream reverse proxying. This is read-only and does not request certificates. Filter domain names by a case-insensitive substring with domain. Filter status with enabled. Set compact=True to return only summary fields. Returns host objects with domains, destination, redirect code, and status."""
        return filter_items(
            self.client.get("/nginx/redirection-hosts"),
            domain=domain,
            enabled=enabled,
            compact=compact,
            compact_keys=(
                "id",
                "domain_names",
                "forward_scheme",
                "forward_domain_name",
                "forward_http_code",
                "certificate_id",
                "enabled",
            ),
        )

    def get_redirection_host(self, id: Annotated[int, Field(description="ID of the redirection host, from the matching list tool.")]) -> dict:
        """Fetch one redirection host by ID with its configured destination and status. Use this for a single redirect; use list_redirection_hosts to discover IDs or inspect all redirects. This is read-only and does not change NPM. Returns the host object with domains, destination, redirect code, and status."""
        validate_positive_id(id)
        return self.client.get(f"/nginx/redirection-hosts/{id}")

    def create_redirection_host(
        self,
        domain_names: Annotated[list[str], Field(description="Domain names routed by this host or certificate.")],
        forward_domain_name: Annotated[str, Field(description="Destination hostname or URL for redirected requests.")],
        forward_http_code: Annotated[int, Field(description="HTTP redirect status: 301, 302, 307, or 308.")] = 302,
        forward_scheme: Annotated[str, Field(description="Scheme of the redirect destination: http or https.")] = "https",
        preserve_path: Annotated[bool, Field(description="Whether to preserve the original request path in the redirect.")] = True,
        ssl_forced: Annotated[bool, Field(description="Whether NPM redirects HTTP requests to HTTPS.")] = False,
        certificate_id: Annotated[Optional[int], Field(description="NPM certificate ID to attach; omit for no certificate.")] = None,
        block_exploits: Annotated[bool, Field(description="Whether NPM enables its exploit-blocking option.")] = True,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Create a host that redirects requests for domains to a destination using the selected HTTP status. Use this for URL redirection; use create_proxy_host to forward requests to an upstream server. NPM stores the redirect configuration; an attached certificate ID is referenced without requesting a certificate. Returns the created host object with its ID and redirect settings. Set dry_run=True to preview the exact request without changing NPM."""
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
        id: Annotated[int, Field(description="ID of the redirection host, from the matching list tool.")],
        domain_names: Annotated[Optional[list[str]], Field(description="Domain names routed by this host or certificate. For updates, omit to keep the current value.")] = None,
        forward_domain_name: Annotated[Optional[str], Field(description="Destination hostname or URL for redirected requests. For updates, omit to keep the current value.")] = None,
        forward_http_code: Annotated[Optional[int], Field(description="HTTP redirect status: 301, 302, 307, or 308. For updates, omit to keep the current value.")] = None,
        forward_scheme: Annotated[Optional[str], Field(description="Scheme of the redirect destination: http or https. For updates, omit to keep the current value.")] = None,
        preserve_path: Annotated[Optional[bool], Field(description="Whether to preserve the original request path in the redirect. For updates, omit to keep the current value.")] = None,
        ssl_forced: Annotated[Optional[bool], Field(description="Whether NPM redirects HTTP requests to HTTPS. For updates, omit to keep the current value.")] = None,
        certificate_id: Annotated[Optional[int], Field(description="NPM certificate ID to attach. Omit to keep the current value.")] = None,
        block_exploits: Annotated[Optional[bool], Field(description="Whether NPM enables its exploit-blocking option. For updates, omit to keep the current value.")] = None,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Update writable settings on an existing redirection host by ID. Use this to change domains, destination, or redirect behavior; use enable_redirection_host or disable_redirection_host for status only. NPM receives the merged writable fields. Returns the updated host object with its redirect settings. Set dry_run=True to preview the exact request without changing NPM."""
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
        existing = update_payload("redirection-hosts", existing, updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/redirection-hosts/{id}", existing)
        return self.client.put(f"/nginx/redirection-hosts/{id}", json=existing)

    def delete_redirection_host(self, id: Annotated[int, Field(description="ID of the redirection host, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> bool | dict:
        """Permanently delete a redirection host by ID, removing its redirect configuration from NPM. Use disable_redirection_host to retain it while stopping redirects; list_redirection_hosts helps verify the ID. Deletion cannot be undone and applies the NPM configuration change. Returns True on success. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/redirection-hosts/{id}")
        return self.client.delete(f"/nginx/redirection-hosts/{id}")

    def enable_redirection_host(self, id: Annotated[int, Field(description="ID of the redirection host, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Enable a disabled redirection host by ID so NPM serves its redirect again. Use update_redirection_host to edit destination or redirect code; list_redirection_hosts shows status. This changes NPM host state and applies its configuration. Returns the updated host object. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/redirection-hosts/{id}/enable")
        return self.client.post(f"/nginx/redirection-hosts/{id}/enable")

    def disable_redirection_host(self, id: Annotated[int, Field(description="ID of the redirection host, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Disable a redirection host by ID while keeping its configuration in NPM. Use delete_redirection_host to remove it; use list_redirection_hosts to check status. This stops the redirect from being served and applies the configuration change. Returns the updated host object. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/redirection-hosts/{id}/disable")
        return self.client.post(f"/nginx/redirection-hosts/{id}/disable")


def register_redirection_host_tools(mcp: FastMCP, client: NPMClient, *, read_only: bool = False) -> None:
    tools = RedirectionHostTools(client)
    register_tools(mcp, (
        tools.list_redirection_hosts,
        tools.get_redirection_host,
        tools.create_redirection_host,
        tools.update_redirection_host,
        tools.delete_redirection_host,
        tools.enable_redirection_host,
        tools.disable_redirection_host,
    ), read_only)
