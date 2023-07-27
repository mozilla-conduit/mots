# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test export functionalities."""

from unittest import mock

import pytest

from mots.export import (
    export_to_format,
    escape_for_rst,
    escape_for_md,
    format_paths_for_rst,
    format_paths_for_md,
    format_people_for_rst,
    format_people_for_md,
    format_review_group_for_rst,
    format_review_group_for_md,
    format_emeritus,
)


@mock.patch("mots.export.Exporter")
def test_export_to_format(exporter):
    directory = mock.MagicMock()
    test = export_to_format(directory, frmt="rst")
    assert test == exporter(directory)._export_to_rst()

    test2 = export_to_format(directory, frmt="md")
    assert test2 == exporter(directory)._export_to_md()

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


def test_escape_for_md():
    test_string = (
        "A couple of backslashes \\ \\\n"
        "A couple of asterisks * *\n"
        "A couple of hashmarks # #\n"
        "A couple of bangs ! !\n"
        "A couple of backticks ` `\n"
        "All on one line: \\ * # ! `"
    )

    expected_string = (
        "A couple of backslashes \\\\ \\\\\n"
        "A couple of asterisks \\* \\*\n"
        "A couple of hashmarks \\# \\#\n"
        "A couple of bangs \\! \\!\n"
        "A couple of backticks \\` \\`\n"
        "All on one line: \\\\ \\* \\# \\! \\`"
    )

    assert expected_string == escape_for_md(test_string)


def test_export_format_paths_for_rst():
    """Ensure outputted strings are correct when formatting paths."""
    mock_directory = mock.MagicMock()
    mock_directory.config_handle.config = {
        "export": {"searchfox_enabled": True},
        "repo": "test-repo",
    }

    paths = ["test_path_1", "test_path_2"]

    assert format_paths_for_rst(paths, indent=8, directory=mock_directory) == (
        "\n        | `test_path_1 "
        "<https://searchfox.org/test-repo/search?q=&path=test_path_1>`__"
        "\n        | `test_path_2 "
        "<https://searchfox.org/test-repo/search?q=&path=test_path_2>`__"
    )

    mock_directory.config_handle.config = {
        "repo": "test-repo",
    }

    paths = ["test_path_1", "test_path_2"]

    assert format_paths_for_rst(paths, indent=8, directory=mock_directory) == (
        "\n        | test_path_1" "\n        | test_path_2"
    )


def test_export_format_paths_for_md():
    """Ensure outputted strings are correct when formatting paths."""
    mock_directory = mock.MagicMock()
    mock_directory.config_handle.config = {
        "export": {"searchfox_enabled": True},
        "repo": "test-repo",
    }

    paths = ["test_path_1", "test_path_2"]

    assert format_paths_for_md(paths, indent=4, directory=mock_directory) == (
        "\n    * [test_path_1]"
        "(https://searchfox.org/test-repo/search?q=&path=test_path_1)"
        "\n    * [test_path_2]"
        "(https://searchfox.org/test-repo/search?q=&path=test_path_2)"
    )

    mock_directory.config_handle.config = {
        "repo": "test-repo",
    }

    paths = ["test_path_1", "test_path_2"]

    assert format_paths_for_md(paths, indent=4, directory=mock_directory) == (
        "\n    * test_path_1" "\n    * test_path_2"
    )


def test_export_format_people_for_rst(config):
    """Ensure outputted strings are correct when formatting people."""
    config["people"].append({"nick": "unnamed"})
    test = format_people_for_rst(config["people"], indent=8)
    assert test == (
        "\n        | `jane (jane) <https://people.mozilla.org/s?query=jane>`__"
        "\n        | `jill (jill) <https://people.mozilla.org/s?query=jill>`__"
        "\n        | `otis (otis) <https://people.mozilla.org/s?query=otis>`__"
        "\n        | `angel (angel) <https://people.mozilla.org/s?query=angel>`__"
        "\n        | `unnamed <https://people.mozilla.org/s?query=unnamed>`__"
    )


def test_export_format_people_for_md(config):
    """Ensure outputted strings are correct when formatting people."""
    config["people"].append({"nick": "unnamed"})
    test = format_people_for_md(config["people"], indent=4)
    assert test == (
        "\n    * [jane (jane)](https://people.mozilla.org/s?query=jane)"
        "\n    * [jill (jill)](https://people.mozilla.org/s?query=jill)"
        "\n    * [otis (otis)](https://people.mozilla.org/s?query=otis)"
        "\n    * [angel (angel)](https://people.mozilla.org/s?query=angel)"
        "\n    * [unnamed](https://people.mozilla.org/s?query=unnamed)"
    )


def test_export_format_emeritus(config):
    emeritus = ["maggie", config["people"][0]]
    test = format_emeritus(emeritus)
    assert test == "maggie, jane"


def test_export_format_review_group_for_rst():
    """Ensure outputted strings are correct when formatting review group."""
    test = format_review_group_for_rst("foo")
    assert test == "`#foo <https://phabricator.services.mozilla.com/tag/foo/>`__"


def test_export_format_review_group_for_md():
    """Ensure outputted strings are correct when formatting review group."""
    test = format_review_group_for_md("foo")
    assert test == "[#foo](https://phabricator.services.mozilla.com/tag/foo/)"
