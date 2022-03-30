# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Integration tests for settings."""

import pytest
from unittest.mock import patch
from mots.settings import Settings


@pytest.fixture
def mock_getenv():
    _vars = {
        "MOTS_KEY_2": "ENV_VALUE_2",
    }
    return lambda key, default=None: _vars.get(key, default)


@pytest.fixture
def mock_settings(monkeypatch):
    mock_defaults = {
        "KEY_1": "SET_VALUE_1",
        "KEY_2": "SET_VALUE_2",
        "KEY_3": "SET_VALUE_3",
    }
    monkeypatch.setattr(Settings, "DEFAULTS", mock_defaults)
    settings = Settings()
    return settings


def test__get_from_settings(mock_settings):
    assert mock_settings.KEY_1 == "SET_VALUE_1"
    assert mock_settings.KEY_2 == "SET_VALUE_2"
    assert mock_settings.KEY_3 == "SET_VALUE_3"


@patch("mots.settings.os.getenv")
def test__get_from_env(getenv, mock_settings, mock_getenv):
    getenv.side_effect = mock_getenv
    mock_settings.load()
    mock_settings.set_attributes()
    assert mock_settings.KEY_1 == "SET_VALUE_1"
    assert mock_settings.KEY_2 == "ENV_VALUE_2"
    assert mock_settings.KEY_3 == "SET_VALUE_3"


@patch("mots.settings.os.getenv")
def test__get_from_overrides(getenv, mock_settings, mock_getenv):
    getenv.side_effect = mock_getenv
    mock_settings.overrides = {
        "KEY_2": "OVERRIDE_VALUE_2",
        "KEY_3": "OVERRIDE_VALUE_3",
    }
    mock_settings.load()
    mock_settings.set_attributes()
    assert mock_settings.KEY_1 == "SET_VALUE_1"
    assert mock_settings.KEY_2 == "OVERRIDE_VALUE_2"
    assert mock_settings.KEY_3 == "OVERRIDE_VALUE_3"
