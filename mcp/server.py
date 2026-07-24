import os
import sys

# Fix: the local 'mcp/' directory shadows the installed 'mcp' package (PyPI).
# Pre-load the real 'mcp' package into sys.modules before fastmcp tries to
# import it, so that fastmcp.exceptions can do `from mcp import McpError`.
if "mcp" not in sys.modules or not hasattr(sys.modules.get("mcp"), "McpError"):
    _saved_path = sys.path[:]
    # Strip paths that would resolve to the local mcp/ directory
    sys.path = [
        p
        for p in sys.path
        if p not in ("", ".")
        and not (p and os.path.isdir(os.path.join(p, "mcp")) and os.path.isfile(
            os.path.join(p, "mcp", "__init__.py")
        ) and not os.path.isfile(os.path.join(p, "mcp", "shared", "exceptions.py")))
    ]
    # Remove any cached local mcp to force a clean lookup
    sys.modules.pop("mcp", None)
    import mcp as _real_mcp  # noqa: F401 — side effect: caches the real mcp
    sys.path = _saved_path

from fastmcp import FastMCP
from starlette.middleware import Middleware

from auth import BearerTokenAuthMiddleware
from npm_client import NPMClient
from tools.proxy_hosts import register_proxy_host_tools
from tools.ssl_certs import register_ssl_cert_tools
from tools.access_lists import register_access_list_tools
from tools.redirection_hosts import register_redirection_host_tools
from tools.streams import register_stream_tools


def validate_env() -> None:
    required = ["NPM_URL", "NPM_EMAIL", "NPM_PASSWORD"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def get_transport() -> str:
    transport = os.environ.get("MCP_TRANSPORT", "sse").lower()
    if transport not in {"sse", "stdio"}:
        print("ERROR: MCP_TRANSPORT must be one of: sse, stdio", file=sys.stderr)
        sys.exit(1)
    return transport


def get_sse_middleware() -> list[Middleware]:
    token = os.environ.get("MCP_BEARER_TOKEN")
    if not token:
        return []
    return [Middleware(BearerTokenAuthMiddleware, token=token)]


mcp = FastMCP("nginx-proxy-manager-mcp")


def build_server() -> FastMCP:
    validate_env()
    client = NPMClient()
    register_proxy_host_tools(mcp, client)
    register_ssl_cert_tools(mcp, client)
    register_access_list_tools(mcp, client)
    register_redirection_host_tools(mcp, client)
    register_stream_tools(mcp, client)
    return mcp


if __name__ == "__main__":
    build_server()
    transport = get_transport()
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.run(transport="sse", host=host, port=port, middleware=get_sse_middleware())
