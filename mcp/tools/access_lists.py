from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from npm_client import NPMClient


class AccessListTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def list_access_lists(self) -> list[dict]:
        """List all access lists."""
        return self.client.get("/nginx/access-lists")

    def get_access_list(self, id: int) -> dict:
        """Get access list detail including IP rules and basic auth users."""
        return self.client.get(f"/nginx/access-lists/{id}")

    def create_access_list(
        self,
        name: str,
        satisfy_any: bool = False,
        pass_auth: bool = False,
        clients: Optional[list[dict]] = None,
        items: Optional[list[dict]] = None,
    ) -> dict:
        """
        Create a new access list.
        clients: [{"address": "1.2.3.4", "directive": "allow|deny"}]
        items: [{"username": "user", "password": "pass"}]
        """
        payload = {
            "name": name,
            "satisfy_any": satisfy_any,
            "pass_auth": pass_auth,
            "clients": clients or [],
            "items": items or [],
        }
        return self.client.post("/nginx/access-lists", json=payload)

    def update_access_list(
        self,
        id: int,
        name: Optional[str] = None,
        satisfy_any: Optional[bool] = None,
        pass_auth: Optional[bool] = None,
        clients: Optional[list[dict]] = None,
        items: Optional[list[dict]] = None,
    ) -> dict:
        """Update an existing access list. Only provided fields are changed."""
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
        existing.update(updates)
        return self.client.put(f"/nginx/access-lists/{id}", json=existing)

    def delete_access_list(self, id: int) -> bool:
        """Delete an access list. Proxy hosts using it will lose access control."""
        return self.client.delete(f"/nginx/access-lists/{id}")


def register_access_list_tools(mcp: FastMCP, client: NPMClient) -> None:
    tools = AccessListTools(client)
    mcp.tool()(tools.list_access_lists)
    mcp.tool()(tools.get_access_list)
    mcp.tool()(tools.create_access_list)
    mcp.tool()(tools.update_access_list)
    mcp.tool()(tools.delete_access_list)
