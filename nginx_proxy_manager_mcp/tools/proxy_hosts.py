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
    validate_email,
    validate_forward_scheme,
    validate_host,
    validate_optional_positive_id,
    validate_port,
    validate_positive_id,
)


class ProxyHostTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_proxy_hosts(
        self,
        domain: Annotated[Optional[str], Field(description="Case-insensitive substring to match against any domain name; omit for all domains.")] = None,
        enabled: Annotated[Optional[bool], Field(description="Keep items with this enabled status; omit for both enabled and disabled items.")] = None,
        compact: Annotated[bool, Field(description="Return only summary fields when True; defaults to full NPM objects.")] = False,
    ) -> list[dict]:
        """List proxy hosts configured in NPM, including their current status. Use this to find host IDs before get, update, enable, disable, or delete operations. It does not change NPM or request a certificate. Filter domain names by a case-insensitive substring with domain. Filter status with enabled. Set compact=True to return only summary fields. Returns a list of host objects with IDs, domains, forwarding settings, and status."""
        return filter_items(
            self.client.get("/nginx/proxy-hosts"),
            domain=domain,
            enabled=enabled,
            compact=compact,
            compact_keys=(
                "id",
                "domain_names",
                "forward_scheme",
                "forward_host",
                "forward_port",
                "certificate_id",
                "ssl_forced",
                "enabled",
            ),
        )

    def get_proxy_host(self, id: Annotated[int, Field(description="ID of the proxy host, from the matching list tool.")]) -> dict:
        """Fetch one proxy host by ID, including its configured fields and current status. Use this for details about one host; use list_proxy_hosts to find IDs or inspect all hosts. This is read-only and does not reload Nginx. Returns the NPM host object, including domains, forwarding settings, and status."""
        validate_positive_id(id)
        return self.client.get(f"/nginx/proxy-hosts/{id}")

    def create_proxy_host(
        self,
        domain_names: Annotated[list[str], Field(description="Domain names routed by this host or certificate.")],
        forward_scheme: Annotated[str, Field(description="Upstream scheme: http or https.")],
        forward_host: Annotated[str, Field(description="Upstream hostname or IP address.")],
        forward_port: Annotated[int, Field(description="Upstream TCP port number.")],
        ssl_forced: Annotated[bool, Field(description="Whether NPM redirects HTTP requests to HTTPS.")] = False,
        certificate_id: Annotated[Optional[int], Field(description="NPM certificate ID to attach; omit for no certificate.")] = None,
        access_list_id: Annotated[Optional[int], Field(description="NPM access-list ID to attach; omit for no access list.")] = None,
        block_exploits: Annotated[bool, Field(description="Whether NPM enables its exploit-blocking option.")] = True,
        caching_enabled: Annotated[bool, Field(description="Whether NPM enables proxy caching.")] = False,
        allow_websocket_upgrade: Annotated[bool, Field(description="Whether NPM allows WebSocket upgrades.")] = False,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Create a proxy host that routes the supplied domains to an HTTP or HTTPS upstream. Use this when configuring proxying without requesting a certificate; use create_proxy_host_with_letsencrypt to request one and force HTTPS. NPM stores the host configuration and applies it through its normal config handling. Returns the created host object with its ID, domains, and forwarding settings. Set dry_run=True to preview the exact request without changing NPM."""
        validate_domain_names(domain_names)
        validate_forward_scheme(forward_scheme)
        validate_host(forward_host, "forward_host")
        validate_port(forward_port, "forward_port")
        validate_optional_positive_id(certificate_id, "certificate_id")
        validate_optional_positive_id(access_list_id, "access_list_id")
        payload = {
            "domain_names": domain_names,
            "forward_scheme": forward_scheme,
            "forward_host": forward_host,
            "forward_port": forward_port,
            "ssl_forced": ssl_forced,
            "certificate_id": certificate_id or 0,
            "access_list_id": access_list_id or 0,
            "block_exploits": block_exploits,
            "caching_enabled": caching_enabled,
            "allow_websocket_upgrade": allow_websocket_upgrade,
            "advanced_config": "",
            "meta": {},
            "locations": [],
        }
        if dry_run:
            return dry_run_preview("POST", "/nginx/proxy-hosts", payload)
        return self.client.post("/nginx/proxy-hosts", json=payload)

    def create_proxy_host_with_letsencrypt(
        self,
        domain_names: Annotated[list[str], Field(description="Domain names routed by this host or certificate.")],
        forward_scheme: Annotated[str, Field(description="Upstream scheme: http or https.")],
        forward_host: Annotated[str, Field(description="Upstream hostname or IP address.")],
        forward_port: Annotated[int, Field(description="Upstream TCP port number.")],
        email: Annotated[str, Field(description="Email address supplied to Let's Encrypt for certificate requests.")],
        access_list_id: Annotated[Optional[int], Field(description="NPM access-list ID to attach; omit for no access list.")] = None,
        block_exploits: Annotated[bool, Field(description="Whether NPM enables its exploit-blocking option.")] = True,
        caching_enabled: Annotated[bool, Field(description="Whether NPM enables proxy caching.")] = False,
        allow_websocket_upgrade: Annotated[bool, Field(description="Whether NPM allows WebSocket upgrades.")] = False,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Request a Let's Encrypt certificate, then create a proxy host using that certificate with HTTPS forced. Use this for a new TLS-enabled proxy; use create_proxy_host when a certificate already exists or HTTPS forcing is not wanted. This triggers a certificate request before creating the host; failures report failed_step and any created certificate. Returns ok plus certificate and proxy_host objects on success. Set dry_run=True to preview the exact request without changing NPM."""
        validate_domain_names(domain_names)
        validate_forward_scheme(forward_scheme)
        validate_host(forward_host, "forward_host")
        validate_port(forward_port, "forward_port")
        validate_email(email)
        validate_optional_positive_id(access_list_id, "access_list_id")
        cert_payload = {
            "provider": "letsencrypt",
            "domain_names": domain_names,
            "meta": {
                "letsencrypt_email": email,
                "letsencrypt_agree": True,
                "dns_challenge": False,
            },
        }
        proxy_payload = {
            "domain_names": domain_names,
            "forward_scheme": forward_scheme,
            "forward_host": forward_host,
            "forward_port": forward_port,
            "ssl_forced": True,
            "certificate_id": "<created certificate id>",
            "access_list_id": access_list_id or 0,
            "block_exploits": block_exploits,
            "caching_enabled": caching_enabled,
            "allow_websocket_upgrade": allow_websocket_upgrade,
            "advanced_config": "",
            "meta": {},
            "locations": [],
        }
        if dry_run:
            return {
                "dry_run": True,
                "steps": [
                    dry_run_preview("POST", "/nginx/certificates", cert_payload),
                    dry_run_preview("POST", "/nginx/proxy-hosts", proxy_payload),
                ],
            }

        try:
            certificate = self.client.post("/nginx/certificates", json=cert_payload)
        except Exception as exc:
            return {
                "ok": False,
                "failed_step": "create_certificate",
                "error": str(exc),
                "created_certificate": None,
                "created_proxy_host": None,
            }

        certificate_id = certificate.get("id") if isinstance(certificate, dict) else None
        if not certificate_id:
            return {
                "ok": False,
                "failed_step": "create_certificate",
                "error": "NPM did not return a certificate id",
                "created_certificate": certificate,
                "created_proxy_host": None,
            }

        proxy_payload["certificate_id"] = certificate_id
        try:
            proxy_host = self.client.post("/nginx/proxy-hosts", json=proxy_payload)
        except Exception as exc:
            return {
                "ok": False,
                "failed_step": "create_proxy_host",
                "error": str(exc),
                "created_certificate": certificate,
                "created_proxy_host": None,
            }

        return {
            "ok": True,
            "certificate": certificate,
            "proxy_host": proxy_host,
        }

    def update_proxy_host(
        self,
        id: Annotated[int, Field(description="ID of the proxy host, from the matching list tool.")],
        domain_names: Annotated[Optional[list[str]], Field(description="Domain names routed by this host or certificate. For updates, omit to keep the current value.")] = None,
        forward_scheme: Annotated[Optional[str], Field(description="Upstream scheme: http or https. For updates, omit to keep the current value.")] = None,
        forward_host: Annotated[Optional[str], Field(description="Upstream hostname or IP address. For updates, omit to keep the current value.")] = None,
        forward_port: Annotated[Optional[int], Field(description="Upstream TCP port number. For updates, omit to keep the current value.")] = None,
        ssl_forced: Annotated[Optional[bool], Field(description="Whether NPM redirects HTTP requests to HTTPS. For updates, omit to keep the current value.")] = None,
        certificate_id: Annotated[Optional[int], Field(description="NPM certificate ID to attach. Omit to keep the current value.")] = None,
        access_list_id: Annotated[Optional[int], Field(description="NPM access-list ID to attach. Omit to keep the current value.")] = None,
        block_exploits: Annotated[Optional[bool], Field(description="Whether NPM enables its exploit-blocking option. For updates, omit to keep the current value.")] = None,
        caching_enabled: Annotated[Optional[bool], Field(description="Whether NPM enables proxy caching. For updates, omit to keep the current value.")] = None,
        allow_websocket_upgrade: Annotated[Optional[bool], Field(description="Whether NPM allows WebSocket upgrades. For updates, omit to keep the current value.")] = None,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Update writable settings on an existing proxy host by ID. Use this to change routing or options; use enable_proxy_host or disable_proxy_host for status only. NPM receives the merged writable host fields, without requesting a certificate. Returns the updated host object with its ID and current settings. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if domain_names is not None:
            validate_domain_names(domain_names)
        if forward_scheme is not None:
            validate_forward_scheme(forward_scheme)
        if forward_host is not None:
            validate_host(forward_host, "forward_host")
        if forward_port is not None:
            validate_port(forward_port, "forward_port")
        validate_optional_positive_id(certificate_id, "certificate_id")
        validate_optional_positive_id(access_list_id, "access_list_id")
        existing = self.client.get(f"/nginx/proxy-hosts/{id}")
        updates = {
            k: v
            for k, v in {
                "domain_names": domain_names,
                "forward_scheme": forward_scheme,
                "forward_host": forward_host,
                "forward_port": forward_port,
                "ssl_forced": ssl_forced,
                "certificate_id": certificate_id,
                "access_list_id": access_list_id,
                "block_exploits": block_exploits,
                "caching_enabled": caching_enabled,
                "allow_websocket_upgrade": allow_websocket_upgrade,
            }.items()
            if v is not None
        }
        existing = update_payload("proxy-hosts", existing, updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/proxy-hosts/{id}", existing)
        return self.client.put(f"/nginx/proxy-hosts/{id}", json=existing)

    def delete_proxy_host(self, id: Annotated[int, Field(description="ID of the proxy host, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> bool | dict:
        """Permanently delete a proxy host by ID, removing its configured domain routing from NPM. Use disable_proxy_host to stop routing while keeping the host; list_proxy_hosts helps confirm the ID. Deletion cannot be undone and NPM applies the configuration change. Returns True on success. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/proxy-hosts/{id}")
        return self.client.delete(f"/nginx/proxy-hosts/{id}")

    def enable_proxy_host(self, id: Annotated[int, Field(description="ID of the proxy host, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Enable a disabled proxy host by ID so NPM serves its configured domain routing again. Use update_proxy_host to change host settings; use list_proxy_hosts to confirm status and ID. This changes NPM host state and applies its configuration. Returns the updated host object. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/proxy-hosts/{id}/enable")
        return self.client.post(f"/nginx/proxy-hosts/{id}/enable")

    def disable_proxy_host(self, id: Annotated[int, Field(description="ID of the proxy host, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Disable a proxy host by ID while retaining its configuration. Use delete_proxy_host to remove it; use list_proxy_hosts to check its current status. This changes NPM host state and stops that host from serving traffic. Returns the updated host object. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/proxy-hosts/{id}/disable")
        return self.client.post(f"/nginx/proxy-hosts/{id}/disable")


def register_proxy_host_tools(mcp: FastMCP, client: NPMClient, *, read_only: bool = False) -> None:
    tools = ProxyHostTools(client)
    register_tools(mcp, (
        tools.list_proxy_hosts,
        tools.get_proxy_host,
        tools.create_proxy_host,
        tools.create_proxy_host_with_letsencrypt,
        tools.update_proxy_host,
        tools.delete_proxy_host,
        tools.enable_proxy_host,
        tools.disable_proxy_host,
    ), read_only)
