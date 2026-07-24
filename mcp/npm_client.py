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


class NPMClient:
    def __init__(self) -> None:
        self.base_url = os.environ["NPM_URL"].rstrip("/")
        self._email = os.environ["NPM_EMAIL"]
        self._password = os.environ["NPM_PASSWORD"]
        self.token: str | None = None
        self._http = httpx.Client(timeout=30)

    def _raise_api_error(self, method: str, path: str, resp: httpx.Response) -> None:
        detail = ""
        if resp.content:
            try:
                body = resp.json()
            except ValueError:
                detail = resp.text.strip()
            else:
                if isinstance(body, dict):
                    detail = str(
                        body.get("message")
                        or body.get("error")
                        or body.get("detail")
                        or body
                    )
                else:
                    detail = str(body)
        if not detail:
            detail = resp.reason_phrase or "request failed"
        raise NPMAPIError(method, path, resp.status_code, detail)

    def _authenticate(self) -> None:
        resp = self._http.post(
            f"{self.base_url}/api/tokens",
            json={"identity": self._email, "secret": self._password},
        )
        if resp.is_error:
            self._raise_api_error("POST", "/tokens", resp)
        self.token = resp.json()["token"]

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self.token:
            self._authenticate()
        resp = self._http.request(
            method,
            f"{self.base_url}/api{path}",
            headers=self._auth_headers(),
            **kwargs,
        )
        if resp.status_code == 401:
            self._authenticate()
            resp = self._http.request(
                method,
                f"{self.base_url}/api{path}",
                headers=self._auth_headers(),
                **kwargs,
            )
        if resp.is_error:
            self._raise_api_error(method, path, resp)
        if not resp.content:
            return None
        return resp.json()

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
