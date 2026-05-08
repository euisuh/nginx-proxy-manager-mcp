import os
import httpx
from typing import Any


class NPMClient:
    def __init__(self) -> None:
        self.base_url = os.environ["NPM_URL"].rstrip("/")
        self._email = os.environ["NPM_EMAIL"]
        self._password = os.environ["NPM_PASSWORD"]
        self.token: str | None = None
        self._http = httpx.Client(timeout=30)

    def _authenticate(self) -> None:
        resp = self._http.post(
            f"{self.base_url}/api/tokens",
            json={"identity": self._email, "secret": self._password},
        )
        resp.raise_for_status()
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
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self.request("DELETE", path, **kwargs)
