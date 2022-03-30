# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Utility helper functions."""

from pathlib import Path
from typing import Optional
import re


def generate_machine_readable_name(display_name, keep_case=False):
    """Turn spaces into underscores, and lower the case. Strip all but alphanumerics."""
    words = [w.strip() for w in display_name.split(" ")]
    if keep_case:
        alnum_words = ["".join([c for c in word if c.isalnum()]) for word in words]
    else:
        alnum_words = [
            "".join([c.lower() for c in word if c.isalnum()]) for word in words
        ]
    return "_".join([w for w in alnum_words if w])


def get_list_input(text: str):
    """Parse comma separated list in user input into a list.

    :param test: the text to prompt the user with
    """
    user_input = input(f"{text}: ").split(",")
    return [e.strip() for e in user_input if e]


def parse_real_name(real_name):
    """Parse real_name into name and info."""
    pattern = re.compile(r"^(?P<name>[\w\ ]+?)?\ ?(?P<info>[\(\[\|\:].*)?$")
    match = pattern.match(real_name)
    if match:
        return match.groupdict()
    else:
        return {"name": None, "info": None}


class Disk:
    """Utilities to read and write settings files and directories to disk."""

    def __init__(self):
        self.home = Path.home()
        self.resource_directory = self.home / ".mots"
        self.overrides_file = self.resource_directory / "settings.yaml"

    def setup_resource_directory(self) -> Path:
        """Create the mots resource directory if it does not exist."""
        if not self.resource_directory.exists():
            self.resource_directory.mkdir()

    def setup_overrides_file(self) -> Path:
        """Create the mots overrides file if it does not exist."""
        if not self.overrides_file.exists():
            self.overrides_file.touch()

    def load_overrides(self) -> Optional[dict]:
        """Load overrides from file and return if available."""
        from mots.yaml import yaml

        if self.overrides_file.exists():
            with self.overrides_file.open("r") as f:
                return yaml.load(f) or {}
        else:
            return {}
