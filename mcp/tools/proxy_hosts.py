from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from npm_client import NPMClient

from tools.previews import dry_run_preview


class ProxyHostTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_proxy_hosts(self) -> list[dict]:
        """List all proxy hosts with their current status."""
        return self.client.get("/nginx/proxy-hosts")

    def get_proxy_host(self, id: int) -> dict:
        """Get a single proxy host by ID."""
        return self.client.get(f"/nginx/proxy-hosts/{id}")

    def create_proxy_host(
        self,
        domain_names: list[str],
        forward_scheme: str,
        forward_host: str,
        forward_port: int,
        ssl_forced: bool = False,
        certificate_id: Optional[int] = None,
        access_list_id: Optional[int] = None,
        block_exploits: bool = True,
        caching_enabled: bool = False,
        allow_websocket_upgrade: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """Create a new proxy host. Set dry_run=True to preview without changing NPM."""
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

    def update_proxy_host(
        self,
        id: int,
        domain_names: Optional[list[str]] = None,
        forward_scheme: Optional[str] = None,
        forward_host: Optional[str] = None,
        forward_port: Optional[int] = None,
        ssl_forced: Optional[bool] = None,
        certificate_id: Optional[int] = None,
        access_list_id: Optional[int] = None,
        block_exploits: Optional[bool] = None,
        caching_enabled: Optional[bool] = None,
        allow_websocket_upgrade: Optional[bool] = None,
        dry_run: bool = False,
    ) -> dict:
        """Update fields on a proxy host. Set dry_run=True to preview the merged payload."""
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
        existing.update(updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/proxy-hosts/{id}", existing)
        return self.client.put(f"/nginx/proxy-hosts/{id}", json=existing)

    def delete_proxy_host(self, id: int, dry_run: bool = False) -> bool | dict:
        """Delete a proxy host permanently. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/proxy-hosts/{id}")
        return self.client.delete(f"/nginx/proxy-hosts/{id}")

    def enable_proxy_host(self, id: int, dry_run: bool = False) -> dict:
        """Enable a previously disabled proxy host. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("POST", f"/nginx/proxy-hosts/{id}/enable")
        return self.client.post(f"/nginx/proxy-hosts/{id}/enable")

    def disable_proxy_host(self, id: int, dry_run: bool = False) -> dict:
        """Disable a proxy host without deleting it. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("POST", f"/nginx/proxy-hosts/{id}/disable")
        return self.client.post(f"/nginx/proxy-hosts/{id}/disable")


def register_proxy_host_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = ProxyHostTools(client)
    mcp.tool()(tools.list_proxy_hosts)
    mcp.tool()(tools.get_proxy_host)
    mcp.tool()(tools.create_proxy_host)
    mcp.tool()(tools.update_proxy_host)
    mcp.tool()(tools.delete_proxy_host)
    mcp.tool()(tools.enable_proxy_host)
    mcp.tool()(tools.disable_proxy_host)
