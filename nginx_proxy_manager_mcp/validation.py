from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable

_DOMAIN_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_REDIRECT_CODES = {300, 301, 302, 303, 307, 308}
_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_ACCESS_DIRECTIVES = {"allow", "deny"}


def validate_positive_id(value: int, field: str = "id") -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def validate_port(value: int, field: str = "port") -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 65535:
        raise ValueError(f"{field} must be an integer between 1 and 65535")
    return value


def validate_forward_scheme(value: str) -> str:
    if value not in _ALLOWED_SCHEMES:
        raise ValueError("forward_scheme must be one of: http, https")
    return value


def validate_redirect_code(value: int) -> int:
    if value not in _ALLOWED_REDIRECT_CODES:
        raise ValueError("forward_http_code must be one of: 300, 301, 302, 303, 307, 308")
    return value


def validate_email(value: str) -> str:
    if not isinstance(value, str) or not _EMAIL_RE.match(value):
        raise ValueError("email must be a valid email address")
    return value


def _validate_hostname(value: str, *, allow_wildcard: bool) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("hostname must be a non-empty string")
    if "://" in value or "/" in value or "?" in value or "#" in value:
        raise ValueError("hostname must not include a URL scheme, path, query, or fragment")
    host = value[:-1] if value.endswith(".") else value
    if allow_wildcard and host.startswith("*."):
        host = host[2:]
    elif "*" in host:
        raise ValueError("wildcards are only allowed as a leading '*.'")
    if not host or len(host) > 253:
        raise ValueError("hostname must be 1-253 characters")
    labels = host.split(".")
    if any(not _DOMAIN_LABEL_RE.match(label) for label in labels):
        raise ValueError("hostname contains an invalid DNS label")
    return value


def validate_host(value: str, field: str = "host") -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty hostname or IP address")
    try:
        ipaddress.ip_address(value)
    except ValueError:
        try:
            _validate_hostname(value, allow_wildcard=False)
        except ValueError as exc:
            raise ValueError(f"{field} is invalid: {exc}") from None
    return value


def validate_domain_names(value: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("domain_names must be a non-empty list")
    seen: set[str] = set()
    for domain in value:
        _validate_hostname(domain, allow_wildcard=True)
        normalized = domain.lower().rstrip(".")
        if normalized in seen:
            raise ValueError("domain_names must not contain duplicates")
        seen.add(normalized)
    return value


def validate_optional_positive_id(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    return validate_positive_id(value, field)


def validate_access_clients(clients: Iterable[dict] | None) -> list[dict]:
    if clients is None:
        return []
    if not isinstance(clients, list):
        raise ValueError("clients must be a list")
    for client in clients:
        if not isinstance(client, dict):
            raise ValueError("each access-list client must be an object")
        directive = client.get("directive")
        if directive not in _ALLOWED_ACCESS_DIRECTIVES:
            raise ValueError("access-list client directive must be 'allow' or 'deny'")
        address = client.get("address")
        if not isinstance(address, str):
            raise ValueError("access-list client address must be a string")
        try:
            ipaddress.ip_network(address, strict=False)
        except ValueError:
            raise ValueError("access-list client address must be a valid IP or CIDR range") from None
    return clients


def validate_access_items(items: Iterable[dict] | None) -> list[dict]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each access-list item must be an object")
        if not item.get("username") or not isinstance(item.get("username"), str):
            raise ValueError("access-list item username must be a non-empty string")
        if not item.get("password") or not isinstance(item.get("password"), str):
            raise ValueError("access-list item password must be a non-empty string")
    return items


def validate_stream_protocols(tcp_forwarding: bool, udp_forwarding: bool) -> None:
    if not isinstance(tcp_forwarding, bool) or not isinstance(udp_forwarding, bool):
        raise ValueError("tcp_forwarding and udp_forwarding must be booleans")
    if not tcp_forwarding and not udp_forwarding:
        raise ValueError("at least one of tcp_forwarding or udp_forwarding must be enabled")
