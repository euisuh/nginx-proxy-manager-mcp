from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from npm_client import NPMClient

from tools.previews import dry_run_preview


class StreamTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_streams(self) -> list[dict]:
        """List all TCP/UDP streams with their current status."""
        return self.client.get("/nginx/streams")

    def get_stream(self, id: int) -> dict:
        """Get a single stream by ID."""
        return self.client.get(f"/nginx/streams/{id}")

    def create_stream(
        self,
        incoming_port: int,
        forwarding_host: str,
        forwarding_port: int,
        tcp_forwarding: bool = True,
        udp_forwarding: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """Create a TCP/UDP stream. Set dry_run=True to preview without changing NPM."""
        payload = {
            "incoming_port": incoming_port,
            "forwarding_host": forwarding_host,
            "forwarding_port": forwarding_port,
            "tcp_forwarding": tcp_forwarding,
            "udp_forwarding": udp_forwarding,
        }
        if dry_run:
            return dry_run_preview("POST", "/nginx/streams", payload)
        return self.client.post("/nginx/streams", json=payload)

    def update_stream(
        self,
        id: int,
        incoming_port: Optional[int] = None,
        forwarding_host: Optional[str] = None,
        forwarding_port: Optional[int] = None,
        tcp_forwarding: Optional[bool] = None,
        udp_forwarding: Optional[bool] = None,
        dry_run: bool = False,
    ) -> dict:
        """Update a stream. Set dry_run=True to preview the merged payload."""
        existing = self.client.get(f"/nginx/streams/{id}")
        updates = {
            k: v
            for k, v in {
                "incoming_port": incoming_port,
                "forwarding_host": forwarding_host,
                "forwarding_port": forwarding_port,
                "tcp_forwarding": tcp_forwarding,
                "udp_forwarding": udp_forwarding,
            }.items()
            if v is not None
        }
        existing.update(updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/streams/{id}", existing)
        return self.client.put(f"/nginx/streams/{id}", json=existing)

    def delete_stream(self, id: int, dry_run: bool = False) -> bool | dict:
        """Delete a stream. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/streams/{id}")
        return self.client.delete(f"/nginx/streams/{id}")

    def enable_stream(self, id: int, dry_run: bool = False) -> dict:
        """Enable a stream. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("POST", f"/nginx/streams/{id}/enable")
        return self.client.post(f"/nginx/streams/{id}/enable")

    def disable_stream(self, id: int, dry_run: bool = False) -> dict:
        """Disable a stream. Set dry_run=True to preview only."""
        if dry_run:
            return dry_run_preview("POST", f"/nginx/streams/{id}/disable")
        return self.client.post(f"/nginx/streams/{id}/disable")


def register_stream_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = StreamTools(client)
    mcp.tool()(tools.list_streams)
    mcp.tool()(tools.get_stream)
    mcp.tool()(tools.create_stream)
    mcp.tool()(tools.update_stream)
    mcp.tool()(tools.delete_stream)
    mcp.tool()(tools.enable_stream)
    mcp.tool()(tools.disable_stream)
