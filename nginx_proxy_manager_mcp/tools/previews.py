from __future__ import annotations

from typing import Any


def dry_run_preview(method: str, path: str, json: Any = None) -> dict[str, Any]:
    """Return a structured preview for a mutating NPM API request."""
    preview: dict[str, Any] = {
        "dry_run": True,
        "method": method,
        "path": path,
    }
    if json is not None:
        preview["json"] = json
    return preview
