## Summary

-
-
-

## Test plan

- [ ] `ruff check .`
- [ ] `pytest -q`
- [ ] `docker compose config --quiet`

## Safety checklist

- [ ] Mutating tools have `dry_run` support.
- [ ] User inputs are validated before NPM API calls.
- [ ] No secrets, tokens, `.env` values, or credentials are committed.
- [ ] Docs/examples use placeholders only.
