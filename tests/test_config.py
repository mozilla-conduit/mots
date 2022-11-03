# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test config module."""

from mots.config import (
    calculate_hashes,
    FileConfig,
    reference_anchor_for_module,
)
from mots.directory import Directory


def test_calculate_hashes(config):
    export = b""
    hashes = calculate_hashes(config, export)[1]

    assert (
        hashes["config"] == "76997b8d70e561c7ec8a21e1cefbc3c658c6d91a"
    ), "Was `conftest.config` changed?"
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


def test_reference_anchor_for_module(repo):
    """Test that a reference to an existing person is correctly updated.

    When a reference to a person references the same person but a different dictionary,
    reference_anchor_for_module should update that reference to reflect the existing
    person.
    """
    file_config = FileConfig(repo / "mots.yml")
    file_config.load()
    directory = Directory(file_config)
    directory.load(full_paths=True)

    module = file_config.config["modules"][0]["submodules"][0]
    owner_emeritus_field = module["meta"]["owners_emeritus"]
    # Check that existing owner emeritus references the person in the roster.
    assert len(owner_emeritus_field) == 1
    assert id(owner_emeritus_field[0]) == id(file_config.config["people"][2])

    # Change owner emeritus to be the first person in the roster.
    new_person = {"name": "jane", "nick": "jane", "bmo_id": 0}
    owner_emeritus_field[0] = new_person

    assert new_person == file_config.config["people"][0]
    assert id(owner_emeritus_field[0]) != id(file_config.config["people"][0])

    key = "owners_emeritus"
    index = 0
    reference_anchor_for_module(
        index, file_config.config["people"][0], key, file_config, directory, module
    )

    assert id(owner_emeritus_field[0]) == id(file_config.config["people"][0])
