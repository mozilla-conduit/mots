# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Module that provides helpers to interact with the PMO API."""

import requests
import os
import logging


logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://people.mozilla.org/api/v4/"
USER_AGENT = "mots"
PMO_COOKIE_ENV_VAR = "PMO_COOKIE"


class PMOClient:
    """A thin wrapper as a PMO API client."""

    def __init__(self, token: str = None, base_url: str = DEFAULT_BASE_URL):
        if not token:
            token = os.getenv("PMO_COOKIE_ENV_VAR")
            if not token:
                raise ValueError(
                    f"{PMO_COOKIE_ENV_VAR} environment variable missing,"
                    " and no other token was explicitly provided"
                )
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
