# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Utility helper functions."""

from __future__ import annotations

from packaging.version import Version
from pathlib import Path
from xml.etree import ElementTree
import logging
import re

import requests

from mots import __version__

logger = logging.getLogger(__name__)

REAL_NAME_RE = re.compile(r"^(?P<name>[\w\ \-]*)?\ ?(?P<info>\W.*)?$")


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
    match = REAL_NAME_RE.match(real_name)
    if not match:
        return {"name": "", "info": real_name}
    data = match.groupdict()
    return {k: v.strip() if v else "" for k, v in data.items()}


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


def check_for_updates(include_pre_releases: bool = False) -> Version | None:
    """
    Show a message if there is a newer version available.

    This method checks the RSS feed on PyPI.
    """
    URL = "https://pypi.org/rss/project/mots/releases.xml"
    response = requests.get(URL)
    result = ElementTree.fromstring(response.content)
    items = result[0].findall("item")
    versions = [Version(item[0].text) for item in items]

    if not include_pre_releases:
        versions = [v for v in versions if not v.is_prerelease]

    newest_version = max(versions)
    if Version(__version__) < newest_version:
        logger.warning(f"A new version of mots is available ({newest_version})")
        logger.warning(f"You are running {__version__}")
        return newest_version
    else:
        logger.debug(f"You are running the latest version of mots ({__version__})")
