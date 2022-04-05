# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Utility helper functions."""

import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


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


def mkdir_if_not_exists(path: Path):
    """Check if a directory exists, if not, create it."""
    if not path.exists():
        path.mkdir()
    elif path.exists() and not path.is_dir():
        logger.warning(f"{path} exists but is not a directory.")


def touch_if_not_exists(path: Path):
    """Check if a file exists, if not, create it."""
    if not path.exists():
        path.touch()
    elif path.exists() and not path.is_file():
        logger.warning(f"{path} exists but is not a file.")
