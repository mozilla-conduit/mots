# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for bmo module."""

from unittest import mock

import pytest

from mots.bmo import BMOClient, BugzillaAPIError


@mock.patch("mots.bmo.requests.get")
def test_bmo__BMOClient__get_users_by_ids_non_200_raises(get):
    get.return_value = mock.Mock(status_code=500, text="Internal Server Error")
    with pytest.raises(BugzillaAPIError, match="500"):
        BMOClient(token="test").get_users_by_ids([1])


@mock.patch("mots.bmo.requests.get")
def test_bmo__BMOClient__get_matches_non_200_raises(get):
    get.return_value = mock.Mock(status_code=401, text="Unauthorized")
    with pytest.raises(BugzillaAPIError, match="401"):
        BMOClient(token="test").get_matches("test")
