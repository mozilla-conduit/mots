# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Utility helper functions."""


def generate_machine_readable_name(display_name):
    """Turn spaces into underscores, and lower the case. Strip all but alphanumerics."""
    words = [w.strip() for w in display_name.split(" ")]
    alnum_words = ["".join([c.lower() for c in word if c.isalnum()]) for word in words]
    return "_".join([w for w in alnum_words if w])
