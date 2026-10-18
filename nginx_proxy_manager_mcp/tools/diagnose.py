from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from nginx_proxy_manager_mcp.npm_client import NPMClient

from nginx_proxy_manager_mcp.tools import register_tools
from nginx_proxy_manager_mcp.validation import validate_domain_names


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _matches(domain: str, names: list[str]) -> bool:
    domain = domain.lower().rstrip(".")
    for name in names:
        name = name.lower().rstrip(".")
        if domain == name or (name.startswith("*.") and domain.endswith(name[1:]) and "." not in domain[: -len(name) + 1]):
            return True
    return False


class DiagnoseTools:
    def __init__(self, client: NPMClient) -> None:
        self.client = client

    def find_host_by_domain(
        self,
        domain: Annotated[str, Field(description="Domain name to match exactly or against stored wildcard domains, case-insensitively.")],
    ) -> dict:
        """Find proxy hosts, redirection hosts, and certificates serving a domain using exact or wildcard matching. This read-only lookup joins hosts to their assigned certificates. Returns compact host summaries with certificate details and certificates matching the domain."""
        validate_domain_names([domain])
        proxy_hosts = self.client.get("/nginx/proxy-hosts")
        redirection_hosts = self.client.get("/nginx/redirection-hosts")
        certificates = self.client.get("/nginx/certificates")
        certificate_by_id = {cert["id"]: cert for cert in certificates}
        result = {}
        host_keys = (
            "id", "domain_names", "forward_scheme", "forward_host", "forward_port",
            "forward_domain_name", "forward_http_code", "enabled", "certificate_id",
        )
        for group, hosts in (("proxy_hosts", proxy_hosts), ("redirection_hosts", redirection_hosts)):
            result[group] = []
            for host in hosts:
                if not _matches(domain, host.get("domain_names", [])):
                    continue
                summary = {key: host[key] for key in host_keys if key in host}
                cert = certificate_by_id.get(host.get("certificate_id"))
                summary["certificate"] = (
                    {key: cert.get(key) for key in ("id", "provider", "expires_on")}
                    if cert is not None else None
                )
                result[group].append(summary)
        result["certificates"] = [
            cert for cert in certificates if _matches(domain, cert.get("domain_names", []))
        ]
        return result

    def list_expiring_certificates(
        self,
        days: Annotated[int, Field(description="Expiry window in days, from 1 to 3650; expired certificates are always included.")] = 30,
    ) -> list[dict]:
        """List certificates expiring within the requested UTC time window, including certificates already expired, sorted by expiry. This read-only lookup also finds hosts using each certificate. Returns certificate summaries with days_left and proxy or redirection host references in used_by."""
        if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 3650:
            raise ValueError("days must be an integer between 1 and 3650")
        proxy_hosts = self.client.get("/nginx/proxy-hosts")
        redirection_hosts = self.client.get("/nginx/redirection-hosts")
        certificates = self.client.get("/nginx/certificates")
        now = _now()
        expiring = []
        for cert in certificates:
            if not cert.get("expires_on"):
                continue
            expires = datetime.fromisoformat(cert["expires_on"].replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires > now + timedelta(days=days):
                continue
            summary = {key: cert.get(key) for key in ("id", "domain_names", "provider", "expires_on")}
            summary["days_left"] = (expires - now).days
            summary["used_by"] = [
                {"type": host_type, "id": host["id"]}
                for host_type, hosts in (("proxy_host", proxy_hosts), ("redirection_host", redirection_hosts))
                for host in hosts
                if host.get("certificate_id") == cert["id"]
            ]
            expiring.append((expires, summary))
        return [summary for _, summary in sorted(expiring, key=lambda item: item[0])]


def register_diagnose_tools(mcp: FastMCP, client: NPMClient, *, read_only: bool = False) -> None:
    tools = DiagnoseTools(client)
    register_tools(mcp, (
        tools.find_host_by_domain,
        tools.list_expiring_certificates,
    ), read_only)
