# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test export functionalities."""

from unittest import mock

import pytest

from mots.export import export_to_format, escape_for_rst


@mock.patch("mots.export.Exporter")
def test_export_to_format(exporter):
    directory = mock.MagicMock()
    test = export_to_format(directory, frmt="rst")
    assert test == exporter(directory)._export_to_rst()

    with pytest.raises(ValueError):
        export_to_format(directory, frmt="unsupported-format")


def test_escape_for_rst():
    test_string = (
        "A couple of backslashes \\ \\\n"
        "A couple of asterisks * *\n"
        "A couple of backticks ` `\n"
        "All on one line: \\ * `"
    )

    expected_string = (
        "A couple of backslashes \\\\ \\\\\n"
        "A couple of asterisks \\* \\*\n"
        "A couple of backticks \\` \\`\n"
        "All on one line: \\\\ \\* \\`"
    )

    assert expected_string == escape_for_rst(test_string)
