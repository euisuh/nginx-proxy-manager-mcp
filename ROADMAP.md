# Roadmap

This project is intentionally small: one MCP server that gives AI assistants safe, typed access to Nginx Proxy Manager. The roadmap focuses on making that use case reliable enough for real homelabs and clear enough for outside contributors.

## Shipped

- Dry-run previews for mutating tools.
- Input validation for domains, schemes, ports, IDs, redirect codes, access-list clients, and stream protocols.
- `create_proxy_host_with_letsencrypt` for the common “subdomain → service → HTTPS” workflow.
- Structured, redacted NPM API errors for MCP clients.
- Proxy host, redirection host, stream, certificate, and access-list tools.
- Versioned multi-arch GHCR container images.
- Optional bearer-token guard for SSE deployments.
- Safer loopback default for bare SSE runs.
- Lightweight CI quality gate with Ruff.

## Next: distribution and MCP directory readiness

- Rename the internal Python package away from `mcp/` to remove the import workaround and make packaging clean.
- Add a minimal `pipx`/`uvx`/stdio installation path for users who do not want Docker.
- Add Smithery/Glama-compatible metadata if the project is accepted by those MCP directories.
- Add example Claude Desktop, Claude Code, Cursor, and Windsurf configuration snippets.

## Next: broader NPM coverage

- 404 hosts and dead hosts.
- Custom certificates: upload/list/renew/delete where supported by the NPM API.
- Users and audit-log read-only tools.

## Next: operational hardening

- Optional allowlist for destructive tools.
- Structured logs with request IDs and redacted credentials.
- Health/readiness endpoint for the SSE sidecar.
- Integration test profile against an ephemeral NPM container.

## Positioning

The public name is `nginx-proxy-manager-mcp` so the repository matches the exact product and search terms people use. Keep README, container image names, MCP directory submissions, and release assets aligned with that name.
