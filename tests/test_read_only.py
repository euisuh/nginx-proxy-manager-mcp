import asyncio

import pytest
from fastmcp import FastMCP

from nginx_proxy_manager_mcp import server


READ_ONLY_NAMES = {
    "list_proxy_hosts", "get_proxy_host", "list_certificates", "get_certificate",
    "list_access_lists", "get_access_list", "list_streams", "get_stream",
    "list_redirection_hosts", "get_redirection_host",
}
MUTATING_NAMES = {
    "create_proxy_host", "create_proxy_host_with_letsencrypt", "update_proxy_host",
    "delete_proxy_host", "enable_proxy_host", "disable_proxy_host",
    "create_letsencrypt_cert", "delete_certificate", "renew_certificate",
    "create_access_list", "update_access_list", "delete_access_list",
    "create_stream", "update_stream", "delete_stream", "enable_stream", "disable_stream",
    "create_redirection_host", "update_redirection_host", "delete_redirection_host",
    "enable_redirection_host", "disable_redirection_host",
}
REGISTRARS = (
    server.register_proxy_host_tools, server.register_ssl_cert_tools,
    server.register_access_list_tools, server.register_stream_tools,
    server.register_redirection_host_tools,
)


def tool_names(mcp):
    return {tool.name for tool in asyncio.run(mcp.list_tools())}


@pytest.mark.parametrize("value, enabled", [
    ("1", True), ("true", True), ("YES", True), ("TrUe", True),
    ("0", False), (None, False), ("false", False), ("", False), ("other", False),
])
def test_build_server_reads_env(monkeypatch, capsys, value, enabled):
    mcp = FastMCP("read-only-env-test")
    monkeypatch.setattr(server, "mcp", mcp)
    monkeypatch.setattr(server, "NPMClient", object)
    for name in ("NPM_URL", "NPM_EMAIL", "NPM_PASSWORD"):
        monkeypatch.setenv(name, "test")
    if value is None:
        monkeypatch.delenv("NPM_READ_ONLY", raising=False)
    else:
        monkeypatch.setenv("NPM_READ_ONLY", value)

    assert server.build_server() is mcp
    names = tool_names(mcp)
    assert READ_ONLY_NAMES <= names
    if enabled:
        assert all(name.startswith(("list_", "get_", "find_")) for name in names)
    else:
        assert MUTATING_NAMES <= names
    assert capsys.readouterr().err == (
        "NPM read-only mode: mutating tools disabled\n" if enabled else ""
    )


def test_register_all_read_only():
    mcp = FastMCP("read-only-test")
    server.register_all(mcp, object(), read_only=True)
    names = tool_names(mcp)
    assert READ_ONLY_NAMES <= names
    assert all(name.startswith(("list_", "get_", "find_")) for name in names)


def test_register_all_read_write():
    mcp = FastMCP("read-write-test")
    server.register_all(mcp, object(), read_only=False)
    assert READ_ONLY_NAMES | MUTATING_NAMES <= tool_names(mcp)


@pytest.mark.parametrize("register", REGISTRARS)
def test_two_argument_registration_unchanged(register):
    default_mcp = FastMCP("default-test")
    explicit_mcp = FastMCP("explicit-test")
    register(default_mcp, object())
    register(explicit_mcp, object(), read_only=False)
    assert tool_names(default_mcp) == tool_names(explicit_mcp)
