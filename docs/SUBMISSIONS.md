# Directory submission drafts

Status: awesome-mcp-servers PR #16295 is open. The other entries are drafts.
The package is on PyPI as `nginx-proxy-manager-mcp-server`.
Configure `NPM_URL`, `NPM_EMAIL`, and `NPM_PASSWORD` locally before launching;
never paste credentials into a directory entry. Use `MCP_TRANSPORT=stdio`.

## Official MCP registry

Destination: [Official MCP Registry](https://registry.modelcontextprotocol.io/).

```text
Name: io.github.euisuh/nginx-proxy-manager-mcp
Description: Manage Nginx Proxy Manager routing, certificates, streams, and access lists with mutation previews and a one-shot HTTPS host workflow.
Install/launch: MCP_TRANSPORT=stdio uvx nginx-proxy-manager-mcp-server
Repository: https://github.com/euisuh/nginx-proxy-manager-mcp
```

Publish with `mcp-publisher login github && mcp-publisher publish` from the repo root, using [`server.json`](../server.json). Ownership is verified through the `mcp-name` marker in the PyPI README. Bump `version` in `server.json` and `pyproject.toml` together on each release.

## awesome-mcp-servers

Destination: [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers).

Ready-to-paste list entry:

```markdown
- [euisuh/nginx-proxy-manager-mcp](https://github.com/euisuh/nginx-proxy-manager-mcp) 🐍 🏠 - Manage Nginx Proxy Manager routing, certificates, streams, and access lists with mutation previews and a one-shot HTTPS host workflow.
```

```text
Install/launch: MCP_TRANSPORT=stdio uvx nginx-proxy-manager-mcp-server
Repository: https://github.com/euisuh/nginx-proxy-manager-mcp
```

## Agensi

Destination: [Agensi](https://www.agensi.io/), which also lists SKILL.md skills.

```text
Name: Nginx Proxy Manager
Description: Manage Nginx Proxy Manager routing, certificates, streams, and access lists with mutation previews and a one-shot HTTPS host workflow.
Install/launch: MCP_TRANSPORT=stdio uvx nginx-proxy-manager-mcp-server
Repository: https://github.com/euisuh/nginx-proxy-manager-mcp
Skill: https://github.com/euisuh/nginx-proxy-manager-mcp/blob/master/skills/nginx-proxy-manager/SKILL.md
```

Optional skill installation from a local checkout:

```bash
mkdir -p ~/.claude/skills/nginx-proxy-manager
cp skills/nginx-proxy-manager/SKILL.md ~/.claude/skills/nginx-proxy-manager/SKILL.md
```

The skill instructs an agent to preview, show the request, obtain approval,
then apply. It requires a configured NPM MCP connection. These drafts do not
assert acceptance by Agensi or a verified submission form.
