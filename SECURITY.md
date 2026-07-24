# Security Policy

This MCP server can administer Nginx Proxy Manager. Treat it like an admin console, not like a public web app.

## Supported versions

The latest tagged release and the current `master` branch receive security fixes. Older releases are best-effort only.

## Reporting a vulnerability

Please open a private vulnerability report through GitHub Security Advisories if available, or contact the maintainer from the GitHub profile linked in the README.

Include:

- affected commit or version,
- deployment mode (`sse` sidecar or `stdio`),
- whether the MCP endpoint was reachable beyond localhost,
- reproduction steps,
- expected vs. actual impact.

## Deployment guidance

- Do not expose the MCP port to the public internet.
- Bind SSE deployments to `127.0.0.1` on the host unless another trusted network boundary exists.
- Bare SSE runs default to `127.0.0.1`; Docker Compose binds the host port to localhost while the container listens on `0.0.0.0` internally.
- Set `MCP_BEARER_TOKEN` for SSE deployments that can be reached beyond localhost.
- Use a dedicated NPM admin account where possible.
- Keep NPM credentials in environment variables or a secrets manager; do not commit `.env`.
- Assume any MCP client that can reach this server can create, update, disable, or delete proxy hosts and certificates.
