import os
import sys

from fastmcp import FastMCP
from starlette.middleware import Middleware

from nginx_proxy_manager_mcp.auth import BearerTokenAuthMiddleware
from nginx_proxy_manager_mcp.npm_client import NPMClient
from nginx_proxy_manager_mcp.tools.access_lists import register_access_list_tools
from nginx_proxy_manager_mcp.tools.proxy_hosts import register_proxy_host_tools
from nginx_proxy_manager_mcp.tools.redirection_hosts import register_redirection_host_tools
from nginx_proxy_manager_mcp.tools.ssl_certs import register_ssl_cert_tools
from nginx_proxy_manager_mcp.tools.streams import register_stream_tools

mcp = FastMCP("nginx-proxy-manager-mcp")


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


def get_host() -> str:
    return os.environ.get("MCP_HOST", "127.0.0.1")


def build_server() -> FastMCP:
    validate_env()
    client = NPMClient()
    register_proxy_host_tools(mcp, client)
    register_ssl_cert_tools(mcp, client)
    register_access_list_tools(mcp, client)
    register_redirection_host_tools(mcp, client)
    register_stream_tools(mcp, client)
    return mcp


def main() -> None:
    build_server()
    transport = get_transport()
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        host = get_host()
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.run(transport="sse", host=host, port=port, middleware=get_sse_middleware())


if __name__ == "__main__":
    main()
