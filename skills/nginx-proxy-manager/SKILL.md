---
name: nginx-proxy-manager
description: Manage Nginx Proxy Manager hosts, HTTPS certificates, streams, and access lists through the configured NPM MCP tools with request previews and user approval.
---

Use these tools when the user asks to expose an app, inspect routing,
manage certificates, or change streams or access lists in NPM.
The MCP server must already be configured for the intended NPM instance.

## Rules

- List the relevant resources before an update; verify the target ID and current state.
- For every mutation, always call with `dry_run=True` first.
- Show the complete request preview (`method`, `path`, and `json` if present).
- For workflows, show every preview in `steps` before requesting approval.
- Apply only after the user approves the shown preview, using the same arguments
  with `dry_run=False`. Changed arguments require a new preview and approval.
- Use `create_proxy_host_with_letsencrypt` for new HTTPS hosts.
- Never delete without explicit user confirmation naming the resource and ID.
- Never request credentials in chat; use the server's configured credentials.
- If the HTTPS workflow fails, report `failed_step` and any created certificate;
  do not retry blindly or delete the certificate without explicit confirmation.

## Example

User: “expose app on port 3000 at blog.example.com”. With upstream `app`
and a user-approved certificate email, call `create_proxy_host_with_letsencrypt`
with `domain_names=["blog.example.com"]`, `forward_scheme="http"`,
`forward_host="app"`, `forward_port=3000`, `email=<approved email>`,
and `dry_run=True`. Show both previews. Apply only after user OK.
