# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test various CLI commands."""

from mots.cli import version
import subprocess


def test__cli__version():
    out = subprocess.check_output(["mots", "--version"])
    assert out.decode("utf-8").strip() == version()
