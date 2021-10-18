# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Utility helper functions."""

import logging
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
    return [o.strip() for o in input(f"{text}: ").split(",") if o]


def parse_user_string(string):
    """Return user data based on provided string.

    Example:
    >>> test = parse_user_string("charlie jones (cj) <cjones@example.org>")
    >>> print(test)
    >>> {"meta": "cj", "email": "cjones@example.org", "name": "charlie jones"}
    """
    logger.debug(f"Parsing provided string {string}...")
    pattern = re.compile(
        r"^((?P<name>([\w\-'.]+)( +[\w\-'.]+)*)\s?)"
        r"(\((?P<meta>.*)\))?\s?(\<(?P<email>.*)\>)?$"
    )
    match = pattern.match(string)
    if match:
        return match.groupdict()
