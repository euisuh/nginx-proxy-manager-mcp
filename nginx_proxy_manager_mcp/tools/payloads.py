from __future__ import annotations

from typing import Any


# NPM backend/schema/paths/nginx/{proxy-hosts,redirection-hosts}/hostID/put.json,
# streams/streamID/put.json, access-lists/listID/put.json requestBody properties.
UPDATE_FIELDS = {
    "proxy-hosts": {
        "domain_names", "forward_scheme", "forward_host", "forward_port",
        "certificate_id", "ssl_forced", "hsts_enabled", "hsts_subdomains",
        "trust_forwarded_proto", "http2_support", "block_exploits", "caching_enabled",
        "allow_websocket_upgrade", "access_list_id", "advanced_config", "enabled",
        "meta", "locations",
    },
    "redirection-hosts": {
        "domain_names", "forward_http_code", "forward_scheme", "forward_domain_name",
        "preserve_path", "certificate_id", "ssl_forced", "hsts_enabled",
        "hsts_subdomains", "http2_support", "block_exploits", "advanced_config", "meta",
    },
    "streams": {
        "incoming_port", "forwarding_host", "forwarding_port", "tcp_forwarding",
        "udp_forwarding", "certificate_id", "meta",
    },
    "access-lists": {"name", "satisfy_any", "pass_auth", "items", "clients"},
}

# NPM backend/schema/common.json: access_items/access_clients items properties.
ACCESS_ENTRY_FIELDS = {
    "items": {"username", "password"},
    "clients": {"address", "directive"},
}


def update_payload(
    resource: str, existing: dict[str, Any], updates: dict[str, Any],
) -> dict[str, Any]:
    """Merge changes while retaining only fields accepted by the NPM PUT schema."""
    payload = {
        key: value for key, value in {**existing, **updates}.items()
        if key in UPDATE_FIELDS[resource]
    }
    if resource == "access-lists":
        for key, fields in ACCESS_ENTRY_FIELDS.items():
            if key in payload:
                payload[key] = [
                    {field: value for field, value in entry.items() if field in fields}
                    for entry in payload[key]
                ]
    return payload
