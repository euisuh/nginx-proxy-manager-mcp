from __future__ import annotations


def filter_items(
    items: list[dict],
    *,
    domain: str | None = None,
    enabled: bool | None = None,
    compact: bool = False,
    compact_keys: tuple[str, ...] = (),
) -> list[dict]:
    """Filter NPM list results and optionally project ordered summary fields."""
    if domain is not None:
        query = domain.casefold()
        items = [
            item
            for item in items
            if any(query in name.casefold() for name in item.get("domain_names", []))
        ]
    if enabled is not None:
        items = [item for item in items if bool(item["enabled"]) == enabled]
    if compact:
        items = [{key: item[key] for key in compact_keys if key in item} for item in items]
    return items
