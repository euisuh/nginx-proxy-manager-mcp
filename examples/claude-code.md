# Claude Code examples

## SSE sidecar

```bash
claude mcp add nginx-proxy-manager http://localhost:8000/sse
```

If `MCP_BEARER_TOKEN` is set, configure your client or gateway to send:

```text
Authorization: Bearer <token>
```

## stdio

```bash
claude mcp add nginx-proxy-manager \
  --env NPM_URL=http://localhost:81 \
  --env NPM_EMAIL=admin@example.com \
  --env NPM_PASSWORD=replace-me \
  --env MCP_TRANSPORT=stdio \
  -- /path/to/nginx-proxy-manager-mcp/.venv/bin/python /path/to/nginx-proxy-manager-mcp/mcp/server.py
```
