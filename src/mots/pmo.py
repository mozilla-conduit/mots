# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Module that provides helpers to interact with the PMO API."""

import requests
import logging

from mots.settings import settings


logger = logging.getLogger(__name__)


class PMOClient:
    """A thin wrapper as a PMO API client."""

    def __init__(self, token: str = None, base_url: str = settings.PMO_URL):
        if not token:
            token = settings.PMO_COOKIE
            if not token:
                raise ValueError(
                    "PMO cookies is missing and no other "
                    "token was explicitly provided"
                )
        self.headers = {"Cookie": token, "User-Agent": settings.USER_AGENT}
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
