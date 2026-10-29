"""Print the README tool table from the registered tools.

Run `python docs/tools_table.py` and paste the output between the
`<!-- tools:start -->` / `<!-- tools:end -->` markers; tests/test_readme.py
fails if the README drifts from the code.
"""

import asyncio

from fastmcp import FastMCP

from nginx_proxy_manager_mcp.server import register_all

CATEGORIES = {
    "proxy_hosts": "Proxy hosts",
    "redirection_hosts": "Redirection hosts",
    "streams": "Streams",
    "ssl_certs": "Certificates",
    "access_lists": "Access lists",
    "diagnose": "Diagnostics",
}
READ_ONLY_PREFIXES = ("list_", "get_", "find_")


def tools_table() -> str:
    mcp = FastMCP("tools-table")
    register_all(mcp, client=None, read_only=False)
    tools = asyncio.run(mcp.list_tools())
    rows = ["| Tool | Category | Read-only | Description |", "|---|---|---|---|"]
    for tool in tools:
        module = tool.fn.__module__.rsplit(".", 1)[-1]
        summary = tool.description.split(". ", 1)[0].rstrip(".") + "."
        read_only = "yes" if tool.name.startswith(READ_ONLY_PREFIXES) else ""
        rows.append(f"| `{tool.name}` | {CATEGORIES[module]} | {read_only} | {summary} |")
    return "\n".join(rows)


if __name__ == "__main__":
    print(tools_table())
