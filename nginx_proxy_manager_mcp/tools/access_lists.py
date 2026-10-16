from __future__ import annotations
from typing import Annotated, Optional, TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from nginx_proxy_manager_mcp.npm_client import NPMClient

from nginx_proxy_manager_mcp.tools.payloads import update_payload
from nginx_proxy_manager_mcp.tools.previews import dry_run_preview
from nginx_proxy_manager_mcp.validation import validate_access_clients, validate_access_items, validate_positive_id


class AccessListTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_access_lists(self) -> list[dict]:
        """List access lists configured in NPM. Use this to find IDs before fetching, updating, or deleting a list; use get_access_list for one list with its rules. This is read-only and does not expose stored passwords. Returns access-list objects with IDs and names."""
        return self.client.get("/nginx/access-lists")

    def get_access_list(self, id: Annotated[int, Field(description="ID of the access list, from the matching list tool.")]) -> dict:
        """Fetch one access list by ID, including its client rules and basic-auth user metadata. Use this for detailed rules; use list_access_lists to discover IDs. NPM does not return stored item passwords, so password values cannot be read back. Returns the access-list object with name, clients, and user entries."""
        validate_positive_id(id)
        return self.client.get(f"/nginx/access-lists/{id}")

    def create_access_list(
        self,
        name: Annotated[str, Field(description="Human-readable name for this access list.")],
        satisfy_any: Annotated[bool, Field(description="Whether satisfying any configured access rule is sufficient.")] = False,
        pass_auth: Annotated[bool, Field(description="Whether NPM passes basic-auth credentials upstream.")] = False,
        clients: Annotated[Optional[list[dict]], Field(description="IP or network rules; each directive must be allow or deny.")] = None,
        items: Annotated[Optional[list[dict]], Field(description="Basic-auth users as username/password pairs; passwords are write-only in NPM.")] = None,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Create an access list containing optional IP allow/deny rules and basic-auth users. Use this to define access controls for hosts; use update_access_list to change an existing list. NPM stores the rules and credentials, while item passwords are write-only and cannot be read back. Returns the created list object with its ID, name, and rules. Set dry_run=True to preview the exact request without changing NPM."""
        validated_clients = validate_access_clients(clients)
        validated_items = validate_access_items(items)
        payload = {
            "name": name,
            "satisfy_any": satisfy_any,
            "pass_auth": pass_auth,
            "clients": validated_clients,
            "items": validated_items,
        }
        if dry_run:
            return dry_run_preview("POST", "/nginx/access-lists", payload)
        return self.client.post("/nginx/access-lists", json=payload)

    def update_access_list(
        self,
        id: Annotated[int, Field(description="ID of the access list, from the matching list tool.")],
        name: Annotated[Optional[str], Field(description="Human-readable name for this access list. For updates, omit to keep the current value.")] = None,
        satisfy_any: Annotated[Optional[bool], Field(description="Whether satisfying any configured access rule is sufficient. For updates, omit to keep the current value.")] = None,
        pass_auth: Annotated[Optional[bool], Field(description="Whether NPM passes basic-auth credentials upstream. For updates, omit to keep the current value.")] = None,
        clients: Annotated[Optional[list[dict]], Field(description="IP or network rules; each directive must be allow or deny. For updates, omit to keep the current value.")] = None,
        items: Annotated[Optional[list[dict]], Field(description="Basic-auth users as username/password pairs; passwords are write-only in NPM. For updates, omit to keep the current value.")] = None,
        dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False,
    ) -> dict:
        """Update writable fields on an existing access list by ID, including client rules and basic-auth users. Use this to edit access controls; use delete_access_list to remove a list. NPM receives the merged writable fields; item passwords are write-only and cannot be read back. Returns the updated list object with its name and rules. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if clients is not None:
            validate_access_clients(clients)
        if items is not None:
            validate_access_items(items)
        existing = self.client.get(f"/nginx/access-lists/{id}")
        updates = {
            k: v
            for k, v in {
                "name": name,
                "satisfy_any": satisfy_any,
                "pass_auth": pass_auth,
                "clients": clients,
                "items": items,
            }.items()
            if v is not None
        }
        existing = update_payload("access-lists", existing, updates)
        if dry_run:
            return dry_run_preview("PUT", f"/nginx/access-lists/{id}", existing)
        return self.client.put(f"/nginx/access-lists/{id}", json=existing)

    def delete_access_list(self, id: Annotated[int, Field(description="ID of the access list, from the matching list tool.")], dry_run: Annotated[bool, Field(description="When True, return the exact request preview without changing NPM.")] = False) -> bool | dict:
        """Permanently delete an access list by ID from NPM. Use update_access_list to retain the list and change its rules; confirm the ID with list_access_lists first. Deletion cannot be undone and may affect hosts that reference the list. Returns True on success. Set dry_run=True to preview the exact request without changing NPM."""
        validate_positive_id(id)
        if dry_run:
            return dry_run_preview("DELETE", f"/nginx/access-lists/{id}")
        return self.client.delete(f"/nginx/access-lists/{id}")


def register_access_list_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = AccessListTools(client)
    mcp.tool()(tools.list_access_lists)
    mcp.tool()(tools.get_access_list)
    mcp.tool()(tools.create_access_list)
    mcp.tool()(tools.update_access_list)
    mcp.tool()(tools.delete_access_list)
