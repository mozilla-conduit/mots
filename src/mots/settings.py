# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Set up the mots environment.

This module fetches various variables either from the environment or config files that
will directly affect the operation of mots after startup.

Variables defined in this module may be overridden by environment variables or
in the overrides file.
"""

import os
from pathlib import Path

from mots import __version__
from mots.yaml import yaml

HOME_DIRECTORY = Path.home()
RESOURCE_DIRECTORY = HOME_DIRECTORY / ".mots"
OVERRIDES_FILE = RESOURCE_DIRECTORY / "settings.yaml"


class Settings:
    """Helper class to convert settings dict to object."""

    DEFAULTS = {
        "BUGZILLA_API_KEY": "",
        "BUGZILLA_URL": "https://bugzilla.mozilla.org/rest",
        "CHECK_PRE_RELEASES": 0,
        "CHECK_FOR_UPDATES": 1,
        "CIRCLECI_TAG_KEY": "CIRCLE_TAG",
        "DEBUG": 0,
        "DEFAULT_CONFIG_FILEPATH": Path("./mots.yaml"),
        "DEFAULT_EXPORT_FORMAT": "rst",
        "LOG_BACKUPS": 5,
        "LOG_FILE": RESOURCE_DIRECTORY / "mots.log",
        "LOG_MAX_SIZE": 1024 * 1024 * 50,
        "OVERRIDES_FILE": OVERRIDES_FILE,
        "PMO_COOKIE": "",
        "PMO_SEARCH_URL": "https://people.mozilla.org/s?query=",
        "PMO_URL": "https://people.mozilla.org/api/v4",
        "RESOURCE_DIRECTORY": RESOURCE_DIRECTORY,
        "SEARCHFOX_BASE_URL": "https://searchfox.org",
        "USER_AGENT": f"mots/{__version__}",
        "VERSION": __version__,
    }

    # NOTE: keys present in SECURE_KEYS will not be added to logs. Users will be
    # prompted using `getpass`, however they will still be stored as cleartext
    # in the settings file, like all other values.
    SECURE_KEYS = ("BUGZILLA_API_KEY",)

    def __init__(self, **kwargs):
        self.settings = {}
        self.overrides = kwargs
        self.load()
        self.set_attributes()

    def load(self):
        """Load settings from environment where possible, or use defaults."""
        # First get type from default, then load values from env if possible.
        self.settings = {
            k: type(v)(os.getenv(f"MOTS_{k}", v)) for k, v in self.DEFAULTS.items()
        }

        # Now, update with override values if possible.
        self.settings.update(self.overrides)

    def set_attributes(self):
        """Set attributes on instance using settings dict."""
        for k, v in self.settings.items():
            setattr(self, k, v)


if OVERRIDES_FILE.exists():
    with OVERRIDES_FILE.open("r") as f:
        overrides = yaml.load(f) or {}
else:
    overrides = {}
settings = Settings(**overrides)
