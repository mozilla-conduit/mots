# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test config module."""

from mots.config import calculate_hashes, FileConfig, check_nested_keys_for_value


def test_calculate_hashes(config):
    export = b""
    hashes = calculate_hashes(config, export)[1]

    assert hashes["config"] == "76997b8d70e561c7ec8a21e1cefbc3c658c6d91a"
    assert hashes["export"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"


def test_FileConfig__check_hashes(repo):
    file_config = FileConfig(repo / "mots.yml")
    file_config.load()
    errors = file_config.check_hashes()
    assert errors == []

    file_config.config["hashes"]["config"] = "asdf"
    file_config.config["hashes"]["export"] = "ghjk"
    errors = file_config.check_hashes()
    assert errors == [
        "Mismatch in config hash detected.",
        "76997b8d70e561c7ec8a21e1cefbc3c658c6d91a does not match asdf",
        "config file is out of date.",
        "Mismatch in export hash detected.",
        "da39a3ee5e6b4b0d3255bfef95601890afd80709 does not match ghjk",
        "export file is out of date.",
    ]


def test_check_nested_keys_for_value():
    test = {"a": {"b": {"c": 1, "d": None}, "e": 2}}

    assert check_nested_keys_for_value(test, ("x", "y", "z")) is False
    assert check_nested_keys_for_value(test, ("a", "b", "c")) is True
    assert check_nested_keys_for_value(test, ("a", "b", "c", "d")) is False
    assert check_nested_keys_for_value(test, ("a", "b", "d")) is False
    assert check_nested_keys_for_value(test, ("a", "b", "d"), boolean=False) is True
