from collections.abc import Callable, Iterable

from fastmcp import FastMCP


def register_tools(mcp: FastMCP, tools: Iterable[Callable], read_only: bool) -> None:
    for tool in tools:
        if not read_only or tool.__name__.startswith(("list_", "get_", "find_")):
            mcp.tool()(tool)
