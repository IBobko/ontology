"""Shared WordPress REST API client and environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from requests import Response
from requests.auth import HTTPBasicAuth


DEFAULT_WP_URL = "https://deconreality.com"


@dataclass(frozen=True)
class WordPressSettings:
    url: str
    username: str | None = None
    app_password: str | None = None

    @classmethod
    def from_environment(cls, default_url: str = DEFAULT_WP_URL) -> "WordPressSettings":
        return cls(
            url=(os.environ.get("WP_URL") or default_url).rstrip("/"),
            username=os.environ.get("WP_USERNAME") or None,
            app_password=os.environ.get("WP_APP_PASSWORD") or None,
        )

    def require_auth(self) -> None:
        if not self.username or not self.app_password:
            raise RuntimeError(
                "WordPress credentials are required. Set WP_USERNAME and "
                "WP_APP_PASSWORD in the environment."
            )


class WordPressClient:
    def __init__(self, settings: WordPressSettings, timeout: int = 30) -> None:
        self.settings = settings
        self.timeout = timeout

    def _auth(self, required: bool) -> HTTPBasicAuth | None:
        if required:
            self.settings.require_auth()
        if self.settings.username and self.settings.app_password:
            return HTTPBasicAuth(self.settings.username, self.settings.app_password)
        return None

    def request(
        self,
        method: str,
        path: str,
        *,
        auth_required: bool = False,
        **kwargs: Any,
    ) -> Response:
        url = f"{self.settings.url}/{path.lstrip('/')}"
        response = requests.request(
            method,
            url,
            auth=self._auth(auth_required),
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def get(self, path: str, **kwargs: Any) -> Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Response:
        return self.request("POST", path, auth_required=True, **kwargs)
