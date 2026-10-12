# Directory submission drafts

Drafts only: nothing has been submitted and no directory PR has been opened.
All launch commands use the Git repository, without assuming a PyPI release.
Configure `NPM_URL`, `NPM_EMAIL`, and `NPM_PASSWORD` locally before launching;
never paste credentials into a directory entry. Use `MCP_TRANSPORT=stdio`.

## Official MCP registry

Destination: [Official MCP Registry](https://registry.modelcontextprotocol.io/).

```text
Name: io.github.euisuh/nginx-proxy-manager-mcp
Description: Manage Nginx Proxy Manager routing, certificates, streams, and access lists with mutation previews and a one-shot HTTPS host workflow.
Install/launch: MCP_TRANSPORT=stdio uvx --from git+https://github.com/euisuh/nginx-proxy-manager-mcp.git nginx-proxy-manager-mcp
Repository: https://github.com/euisuh/nginx-proxy-manager-mcp
```

This is entry copy, not a publishable `server.json`. The official registry
requires namespace authentication and package ownership verification; a Git
launch command alone does not satisfy its package requirements. Prepare a
supported published package and registry metadata before submission, following
the [official requirements](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md).

## awesome-mcp-servers

Destination: [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers).

Ready-to-paste list entry:

```markdown
- [euisuh/nginx-proxy-manager-mcp](https://github.com/euisuh/nginx-proxy-manager-mcp) 🐍 🏠 - Manage Nginx Proxy Manager routing, certificates, streams, and access lists with mutation previews and a one-shot HTTPS host workflow.
```

```text
Install/launch: MCP_TRANSPORT=stdio uvx --from git+https://github.com/euisuh/nginx-proxy-manager-mcp.git nginx-proxy-manager-mcp
Repository: https://github.com/euisuh/nginx-proxy-manager-mcp
```

## Agensi

Destination: [Agensi](https://www.agensi.io/), which also lists SKILL.md skills.

```text
Name: Nginx Proxy Manager
Description: Manage Nginx Proxy Manager routing, certificates, streams, and access lists with mutation previews and a one-shot HTTPS host workflow.
Install/launch: MCP_TRANSPORT=stdio uvx --from git+https://github.com/euisuh/nginx-proxy-manager-mcp.git nginx-proxy-manager-mcp
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
