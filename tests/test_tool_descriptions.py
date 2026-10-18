import asyncio

from fastmcp import FastMCP

from nginx_proxy_manager_mcp.server import (
    register_access_list_tools,
    register_diagnose_tools,
    register_proxy_host_tools,
    register_redirection_host_tools,
    register_ssl_cert_tools,
    register_stream_tools,
)


class UnusedNPMClient:
    pass


def registered_tools():
    mcp = FastMCP("tool-description-test")
    client = UnusedNPMClient()
    register_proxy_host_tools(mcp, client)
    register_ssl_cert_tools(mcp, client)
    register_access_list_tools(mcp, client)
    register_redirection_host_tools(mcp, client)
    register_stream_tools(mcp, client)
    register_diagnose_tools(mcp, client)
    return asyncio.run(mcp.list_tools())


def test_registered_tool_descriptions_are_complete():
    tools = registered_tools()
    assert len(tools) == 32

    for tool in tools:
        assert len(tool.description or "") >= 140, tool.name
        assert "Returns" in tool.description, tool.name
        if tool.name.startswith(("create_", "update_", "delete_", "enable_", "disable_", "renew_")):
            assert "dry_run" in tool.description, tool.name

        for name, prop in tool.parameters.get("properties", {}).items():
            assert prop.get("description", "").strip(), f"{tool.name}.{name}"
