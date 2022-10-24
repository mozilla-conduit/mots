# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test config module."""

from mots.config import calculate_hashes, FileConfig, clean


def test_calculate_hashes(config):
    export = b""
    hashes = calculate_hashes(config, export)[1]

    assert hashes["config"] == "6ef5f3ed90c5d9aa2eec7b91ed65a78b886e8fa1"
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
        "6ef5f3ed90c5d9aa2eec7b91ed65a78b886e8fa1 does not match asdf",
        "config file is out of date.",
        "Mismatch in export hash detected.",
        "da39a3ee5e6b4b0d3255bfef95601890afd80709 does not match ghjk",
        "export file is out of date.",
    ]


def test_clean_with_no_nick(repo, config_with_bmo_ids_only):
    """Ensures clean function runs without any errors if nick is missing."""
    file_config = FileConfig(repo / "mots.yml")
    file_config.config = config_with_bmo_ids_only
    file_config.write()
    clean(file_config)
