"""Module that provides helpers to interact with the Bugzilla API."""

# TODO: this should be abstracted so that it can be hot-swappable with any API that can
# be searched.

from __future__ import annotations
import requests
import os
import logging
import time


logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://bugzilla.mozilla.org/rest"
USER_AGENT = "mots"  # TODO: improve this and include version.

# TODO set NO_INPUT var to prevent prompt.


class BMOClient:
    """A thin wrapper as a Bugzilla API client."""

    def __init__(self, token: str = None, base_url: str = DEFAULT_BASE_URL):
        if not token:
            token = os.getenv("BUGZILLA_API_KEY", "")
            if not token:
                token = input("Enter BMO Token: ")
            if not token:
                raise Exception()
        self.headers = {"X-BUGZILLA-API-KEY": token, "User-Agent": USER_AGENT}
        self.base_url = base_url

    def _get(self, path: str, params=None):
        logger.debug(f"GET {self.base_url}/{path}")
        params = params or {}
        response = requests.get(
            f"{self.base_url}/{path}", headers=self.headers, params=params
        )
        return response

    def get_user(self, email: str, rate_limit_delay: float = 0.3):
        """Get user data based on provided email address."""
        time.sleep(rate_limit_delay)
        fields = ["real_name", "nick", "email", "name", "id"]
        response = self._get(
            "user", {"names": email, "include_fields": ",".join(fields)}
        )
        if response.status_code != 200:
            logger.error(f"Error searching {email}: {response.status_code}")
            return

        # TODO: handle case when there is more than one match.
        # Since possibly users can sneak in their email address in another field?
        # Although we should validate the "email" field in BMO response + check for
        # verification.

        result = response.json()
        return result["users"][0]

    def get_user_by_id(self, id_: str = "", rate_limit_delay: float = 0.3):
        """Get user data by BMO ID."""
        time.sleep(rate_limit_delay)
        fields = ["real_name", "nick", "name", "id"]
        response = self._get("user", {"ids": id_, "include_fields": ",".join(fields)})
        if response.status_code != 200:
            logger.error(f"Error searching {id_}: {response.status_code}")
            return

        result = response.json()
        return result["users"][0]

    def get_users_by_ids(self, ids: list[str], rate_limit_delay: float = 0.3):
        """Get user data by BMO ID."""
        time.sleep(rate_limit_delay)
        fields = ["real_name", "nick", "name", "id", "email"]
        response = self._get("user", {"ids": ids, "include_fields": ",".join(fields)})
        if response.status_code != 200:
            logger.error(f"Error searching {ids}: {response.status_code}")
            return

        result = response.json()
        return {u["id"]: u for u in result["users"]}

    def get_match(self, match: str, rate_limit_delay: float = 0.3):
        """Get user data based on provided info."""
        time.sleep(rate_limit_delay)
        fields = ["real_name", "nick", "email", "name", "id"]
        response = self._get(
            "user", {"match": match, "include_fields": ",".join(fields)}
        )
        if response.status_code != 200:
            logger.error(f"Error searching {match}: {response.status_code}")
            return

        result = response.json()
        if result["users"]:
            return result["users"][0]
        else:
            return None
        return result["users"][0]

    # NOTES:
    # How to store people?
    # 64523: glob  -> if nick is available
    # 65182: Jane Smith  -> if nick is not available, use provided name.
    # OR
    # - Masayuki Nakano bmo:19563
