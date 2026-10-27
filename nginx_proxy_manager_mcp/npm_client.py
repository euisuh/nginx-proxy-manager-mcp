import os
from typing import Any

import httpx


class NPMAPIError(RuntimeError):
    """Actionable, redacted error from the Nginx Proxy Manager API."""

    def __init__(self, method: str, path: str, status_code: int, detail: str) -> None:
        self.method = method.upper()
        self.path = path
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"NPM API {self.method} {self.path} failed: HTTP {status_code}: {detail}")


class NPMConnectionError(RuntimeError):
    """NPM could not be reached (DNS, refused connection, timeout, TLS)."""


class NPMClient:
    def __init__(self) -> None:
        self.base_url = os.environ["NPM_URL"].rstrip("/")
        self._email = os.environ["NPM_EMAIL"]
        self._password = os.environ["NPM_PASSWORD"]
        self.token: str | None = None
        self._version: tuple[int, int] | None = None
        self._http = httpx.Client(timeout=30)

    def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            return self._http.request(method, f"{self.base_url}/api{path}", **kwargs)
        except httpx.RequestError as exc:
            # httpx messages carry the URL only, never request headers or bodies.
            raise NPMConnectionError(
                f"Cannot reach NPM at {self.base_url} ({method.upper()} {path}): "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    def _raise_api_error(self, method: str, path: str, resp: httpx.Response) -> None:
        detail = ""
        if resp.content:
            try:
                body = resp.json()
            except ValueError:
                detail = resp.text.strip()
            else:
                if isinstance(body, dict):
                    error = body.get("error")
                    # NPM's error handler responds with {"error": {"code": ..., "message": ...}}.
                    if isinstance(error, dict) and error.get("message"):
                        error = error["message"]
                    detail = str(body.get("message") or error or body.get("detail") or body)
                else:
                    detail = str(body)
        if not detail:
            detail = resp.reason_phrase or "request failed"
        raise NPMAPIError(method, path, resp.status_code, detail)

    def _authenticate(self) -> None:
        resp = self._send(
            "POST", "/tokens", json={"identity": self._email, "secret": self._password},
        )
        if resp.is_error:
            self._raise_api_error("POST", "/tokens", resp)
        self.token = resp.json()["token"]

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self.token:
            self._authenticate()
        resp = self._send(method, path, headers=self._auth_headers(), **kwargs)
        if resp.status_code == 401:
            self._authenticate()
            resp = self._send(method, path, headers=self._auth_headers(), **kwargs)
        if resp.is_error:
            self._raise_api_error(method, path, resp)
        if not resp.content:
            return None
        return resp.json()

    def npm_version(self) -> tuple[int, int]:
        """(major, minor) from NPM's unauthenticated GET /api/, cached per process."""
        if self._version is None:
            resp = self._send("GET", "/")
            if resp.is_error:
                self._raise_api_error("GET", "/", resp)
            version = resp.json().get("version") or {}
            # ponytail: builds that report no version are assumed current (>= 2.13).
            self._version = (int(version.get("major", 2)), int(version.get("minor", 13)))
        return self._version

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "NPMClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
