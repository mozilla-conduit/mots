"""Module that provides helpers to interact with the PMO API."""

import requests
import os
import logging


logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://people.mozilla.org/api/v4/"
USER_AGENT = "mots"  # TODO: improve this and include version.


class PMOClient:
    """A thin wrapper as a PMO API client."""

    def __init__(self, token: str = None, base_url: str = DEFAULT_BASE_URL):
        if not token:
            token = os.getenv("PMO_COOKIE", input("Enter PMO Cookie: "))
            if not token:
                raise Exception()
        self.headers = {"Cookie": token, "User-Agent": USER_AGENT}
        self.base_url = base_url

    def _get(self, path: str, params=None):
        params = params or {}
        response = requests.get(
            f"{self.base_url}/{path}", headers=self.headers, params=params
        )
        return response

    def search(self, email: str):
        """Search PMO for a particular email."""
        params = {"q": email, "w": "all"}
        path = "search/simple/"

        return self._get(path, params).json()
