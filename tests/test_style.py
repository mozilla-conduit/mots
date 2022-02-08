# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Python code style tests."""

import subprocess


def test_check_black():
    """Check that black runs cleanly and that no files require reformatting."""
    cmd = ("black", "--diff", "src/mots")
    output = subprocess.check_output(cmd)
    assert not output


def test_check_flake8():
    """Check that flake8 runs cleanly and does not produce any errors."""
    cmd = ("flake8", "--exit-zero", "tests", "src")
    output = subprocess.check_output(cmd)
    if output:
        raise AssertionError(output.decode("utf-8"))
