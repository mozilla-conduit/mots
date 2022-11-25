# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Module that provides helpers to interact with the Bugzilla API."""

from __future__ import annotations

import requests
import logging

from mots.settings import settings


logger = logging.getLogger(__name__)


class MissingBugzillaAPIKey(Exception):
    """Raised when a Bugzilla API key was not detected in settings."""

    pass


def get_bmo_data(people: list) -> dict:
    """Fetch an updated dictionary from Bugzilla with user data.

    Dictionary keys are set to user IDs, and values are set to various data.
    """
    bmo_client = BMOClient()
    bmo_data = bmo_client.get_users_by_ids([p["bmo_id"] for p in people])
    return bmo_data


class BMOClient:
    """A thin wrapper as a Bugzilla API client."""

    def __init__(self, token: str | None = None, base_url: str = settings.BUGZILLA_URL):
        if not token:
            token = settings.BUGZILLA_API_KEY
            if not token:
                raise MissingBugzillaAPIKey()
        self._headers = {"X-BUGZILLA-API-KEY": token, "User-Agent": settings.USER_AGENT}
        self._base_url = base_url

    def _get(self, path: str, params=None):
        logger.debug(f"GET {self._base_url}/{path}")
        params = params or {}
        response = requests.get(
            f"{self._base_url}/{path}", headers=self._headers, params=params
        )
        return response

    def get_users_by_ids(self, ids: list[str]):
        """Get user data by BMO IDs."""
        fields = ["real_name", "nick", "name", "id", "email"]
        response = self._get("user", {"ids": ids, "include_fields": ",".join(fields)})
        if response.status_code != 200:
            logger.error(f"Error searching {ids}: {response.status_code}")
            return

        result = response.json()
        return {u["id"]: u for u in result["users"]}

    def get_matches(self, match: str) -> list[dict]:
        """Get user data based on provided info."""
        fields = ["real_name", "nick", "email", "name", "id"]
        response = self._get(
            "user", {"match": match, "include_fields": ",".join(fields)}
        )
        if response.status_code != 200:
            logger.error(f"Error searching {match}: {response.status_code}")
            return

        result = response.json()
        return result["users"]
