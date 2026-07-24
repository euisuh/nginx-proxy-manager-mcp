# Contributing

Thanks for helping improve Nginx Proxy Manager MCP.

## Local setup

```bash
git clone https://github.com/euisuh/nginx-proxy-manager-mcp.git
cd nginx-proxy-manager-mcp
python -m venv .venv
. .venv/bin/activate
pip install -e . -r requirements-dev.txt
```

## Quality checks

Run the same checks CI runs before opening a PR:

```bash
ruff check .
pytest -q
docker compose config --quiet
```

`docker compose config --quiet` may warn when local `NPM_EMAIL` or `NPM_PASSWORD` are unset; that is expected for config-only validation.

## Development guidelines

- Keep tools narrow and typed; mirror Nginx Proxy Manager API resource names.
- Add `dry_run` support for every mutating tool.
- Validate user-provided inputs before sending requests to NPM.
- Never log or commit NPM credentials, bearer tokens, or `.env` files.
- Add offline tests with mocked NPM responses; do not require a live public certificate issuance path in CI.

## Pull requests

Use conventional commit-style titles when possible:

- `feat: add dead-host tools`
- `fix: handle empty NPM error responses`
- `docs: add Cursor MCP config example`
- `ci: add integration smoke workflow`
