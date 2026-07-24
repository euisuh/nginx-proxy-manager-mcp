# Roadmap

This project is intentionally small: one MCP server that gives AI assistants safe, typed access to Nginx Proxy Manager. The roadmap focuses on making that use case reliable enough for real homelabs and clear enough for outside contributors.

## Shipped

- Dry-run previews for mutating tools.
- Input validation for domains, schemes, ports, IDs, redirect codes, access-list clients, and stream protocols.
- `create_proxy_host_with_letsencrypt` for the common “subdomain → service → HTTPS” workflow.
- Structured, redacted NPM API errors for MCP clients.
- Proxy host, redirection host, stream, certificate, and access-list tools.
- Versioned multi-arch GHCR container images.
- Clean internal `nginx_proxy_manager_mcp` Python package layout.
- Python package build validation on release tags.
- Smithery and Glama registry metadata files.
- Optional bearer-token guard for SSE deployments.
- Unauthenticated `/healthz` liveness endpoint for SSE sidecars.
- Safer loopback default for bare SSE runs.
- Lightweight CI quality gate with Ruff.

## Next: distribution and MCP directory readiness

- Publish the built wheel to PyPI once trusted publishing is configured.
- Submit the repository to Smithery, Glama, PulseMCP, and MCP.so.

## Next: broader NPM coverage

- 404 hosts and dead hosts.
- Custom certificates: upload/list/renew/delete where supported by the NPM API.
- Users and audit-log read-only tools.

## Next: operational hardening

- Optional allowlist for destructive tools.
- Structured logs with request IDs and redacted credentials.
- Readiness endpoint that verifies NPM API reachability without leaking credentials.
- Integration test profile against an ephemeral NPM container.

## Positioning

The public name is `nginx-proxy-manager-mcp` so the repository matches the exact product and search terms people use. Keep README, container image names, MCP directory submissions, and release assets aligned with that name.
