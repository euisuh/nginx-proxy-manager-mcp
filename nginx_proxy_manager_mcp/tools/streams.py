from __future__ import annotations
from typing import Annotated, Optional, TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from nginx_proxy_manager_mcp.npm_client import NPMClient

from nginx_proxy_manager_mcp.tools import register_tools
from nginx_proxy_manager_mcp.tools.payloads import update_payload
from nginx_proxy_manager_mcp.tools.previews import dry_run_preview
from nginx_proxy_manager_mcp.validation import (
    validate_host,
    validate_port,
    validate_positive_id,
    validate_stream_protocols,
)


class StreamTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_streams(self) -> list[dict]:
        """List configured TCP/UDP streams and their current status. Use this to find stream IDs before fetching, changing, enabling, disabling, or deleting a port forward. This is read-only and does not change NPM. Returns stream objects with IDs, incoming and forwarding ports, protocols, and status."""
        return self.client.get("/nginx/streams")

    def get_stream(self, id: Annotated[int, Field(description="ID of the stream, from the matching list tool.")]) -> dict:
        """Fetch one TCP/UDP stream by ID, including its forwarding ports and protocol settings. Use this for one stream; use list_streams to find IDs or inspect all streams. This is read-only and does not change NPM. Returns the stream object with incoming port, destination, protocol flags, and status."""
        validate_positive_id(id)
        return self.client.get(f"/nginx/streams/{id}")

    def create_stream(
        self,
        incoming_port: Annotated[int, Field(description="Public TCP/UDP port number accepted by this stream.")],
        forwarding_host: Annotated[str, Field(description="Hostname or IP address receiving stream traffic.")],
        forwarding_port: Annotated[int, Field(description="Destination TCP/UDP port number.")],
        tcp_forwarding: Annotated[bool, Field(description="Whether this stream forwards TCP traffic.")] = True,
        udp_forwarding: Annotated[bool, Field(description="Whether this stream forwards UDP traffic.")] = False,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Create a TCP/UDP port forward from an incoming port to a destination host and port. Use this for raw TCP or UDP forwarding; use proxy-host tools for HTTP/HTTPS domain routing. NPM stores the stream configuration and applies it through normal config handling. Returns the created stream object with its ID, ports, and protocol flags. Set dry_run=True to preview the exact request without changing NPM."""
        validate_port(incoming_port, "incoming_port")
        validate_host(forwarding_host, "forwarding_host")
        validate_port(forwarding_port, "forwarding_port")
        validate_stream_protocols(tcp_forwarding, udp_forwarding)
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
        id: Annotated[int, Field(description="ID of the stream, from the matching list tool.")],
        incoming_port: Annotated[Optional[int], Field(description="Public TCP/UDP port number accepted by this stream. For updates, omit to keep the current value.")] = None,
        forwarding_host: Annotated[Optional[str], Field(description="Hostname or IP address receiving stream traffic. For updates, omit to keep the current value.")] = None,
        forwarding_port: Annotated[Optional[int], Field(description="Destination TCP/UDP port number. For updates, omit to keep the current value.")] = None,
        tcp_forwarding: Annotated[Optional[bool], Field(description="Whether this stream forwards TCP traffic. For updates, omit to keep the current value.")] = None,
        udp_forwarding: Annotated[Optional[bool], Field(description="Whether this stream forwards UDP traffic. For updates, omit to keep the current value.")] = None,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Update writable port, destination, or protocol fields on an existing stream by ID. Use this to edit forwarding; use enable_stream or disable_stream to change status only. NPM receives the merged writable fields, preserving omitted values. Returns the updated stream object with its forwarding settings. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if incoming_port is not None:
            validate_port(incoming_port, "incoming_port")
        if forwarding_host is not None:
            validate_host(forwarding_host, "forwarding_host")
        if forwarding_port is not None:
            validate_port(forwarding_port, "forwarding_port")
        existing = self.client.get(f"/nginx/streams/{id}")
        merged_tcp = tcp_forwarding if tcp_forwarding is not None else existing.get("tcp_forwarding", True)
        merged_udp = udp_forwarding if udp_forwarding is not None else existing.get("udp_forwarding", False)
        validate_stream_protocols(merged_tcp, merged_udp)
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
        existing = update_payload("streams", existing, updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/streams/{id}", existing)
        return self.client.put(f"/nginx/streams/{id}", json=existing)

    def delete_stream(self, id: Annotated[int, Field(description="ID of the stream, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> bool | dict:
        """Permanently delete a TCP/UDP stream by ID; NPM stops forwarding that port immediately and this cannot be undone. List streams first to confirm the ID. Returns True on success. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/streams/{id}")
        return self.client.delete(f"/nginx/streams/{id}")

    def enable_stream(self, id: Annotated[int, Field(description="ID of the stream, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Enable a disabled TCP/UDP stream by ID so NPM forwards its incoming port again. Use update_stream to change ports or protocol flags; list_streams shows current status. This changes the stream state in NPM. Returns the updated stream object. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/streams/{id}/enable")
        return self.client.post(f"/nginx/streams/{id}/enable")

    def disable_stream(self, id: Annotated[int, Field(description="ID of the stream, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> dict:
        """Disable a TCP/UDP stream by ID while retaining its forwarding configuration. Use delete_stream to remove it; list_streams shows current status. NPM stops forwarding this stream while disabled. Returns the updated stream object. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("POST", f"/nginx/streams/{id}/disable")
        return self.client.post(f"/nginx/streams/{id}/disable")


def register_stream_tools(mcp: FastMCP, client: NPMClient, *, read_only: bool = False) -> None:
    tools = StreamTools(client)
    register_tools(mcp, (
        tools.list_streams,
        tools.get_stream,
        tools.create_stream,
        tools.update_stream,
        tools.delete_stream,
        tools.enable_stream,
        tools.disable_stream,
    ), read_only)
