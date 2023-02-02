# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Test config module."""

from operator import itemgetter
from unittest import mock

import pytest

from mots.config import (
    FileConfig,
    calculate_hashes,
    clean,
    reference_anchor_for_module,
)
from mots.directory import Directory


@pytest.fixture
def test_bmo_user_data():
    return {
        0: {"real_name": "janeway", "nick": "captain", "bmo_id": 0},
        1: {"real_name": "tuvok", "nick": "2vk", "bmo_id": 1},
        2: {"real_name": "neelix", "nick": "cooks4u", "bmo_id": 2},
        3: {"real_name": "seven", "nick": "nanotubes", "bmo_id": 3},
        4: {"real_name": "tom paris", "nick": "paris", "bmo_id": 4},
    }


def test_calculate_hashes(config):
    export = b""
    hashes = calculate_hashes(config, export)[1]

    assert (
        hashes["config"] == "f14a84e9e7a9f39ece7ac7232e2f55dda4da6e54"
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
        "f14a84e9e7a9f39ece7ac7232e2f55dda4da6e54 does not match asdf",
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


@mock.patch("mots.config.get_bmo_data")
def test_clean_removed_user_no_refresh(get_bmo_data, repo, config, test_bmo_user_data):
    """Test that removing a user without a refresh has no effect."""
    get_bmo_data.return_value = test_bmo_user_data

    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    assert file_config.config["people"] == config["people"]

    file_config.config["people"].pop()
    file_config.write()

    clean(file_config, refresh=False)

    cleaned_and_sorted = sorted(file_config.config["people"], key=itemgetter("bmo_id"))
    assert len(cleaned_and_sorted) == 3
    for i, person in enumerate(cleaned_and_sorted):
        assert person == file_config.config["people"][i]


@mock.patch("mots.config.get_bmo_data")
def test_clean_removed_user_with_refresh(
    get_bmo_data, repo, config, test_bmo_user_data
):
    """Test that removing a user with a refresh updates from BMO."""
    get_bmo_data.return_value = test_bmo_user_data

    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    assert file_config.config["people"] == config["people"]

    file_config.config["people"].pop()
    file_config.write()

    clean(file_config, refresh=True)

    cleaned_and_sorted = sorted(file_config.config["people"], key=itemgetter("bmo_id"))
    assert len(cleaned_and_sorted) == 3
    for i, person in enumerate(cleaned_and_sorted):
        assert person["name"] == test_bmo_user_data[i]["real_name"]
        assert person["nick"] == test_bmo_user_data[i]["nick"]


@mock.patch("mots.config.get_bmo_data")
def test_clean_changed_names(get_bmo_data, repo, config, test_bmo_user_data):
    """Test that updated BMO data will be reflected when cleaning."""
    get_bmo_data.return_value = test_bmo_user_data

    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    assert file_config.config["people"] == config["people"]

    clean(file_config)

    for person in file_config.config["people"]:
        assert person["name"] == test_bmo_user_data[person["bmo_id"]]["real_name"]
        assert person["nick"] == test_bmo_user_data[person["bmo_id"]]["nick"]


@mock.patch("mots.config.get_bmo_data")
def test_clean_changed_names_no_refresh(get_bmo_data, repo, config, test_bmo_user_data):
    """Test that updated BMO data has no effect when cleaning without refresh."""
    get_bmo_data.return_value = test_bmo_user_data

    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    assert file_config.config["people"] == config["people"]

    clean(file_config, refresh=False)

    assert sorted(file_config.config["people"], key=itemgetter("bmo_id")) == sorted(
        config["people"], key=itemgetter("bmo_id")
    )


@mock.patch("mots.config.get_bmo_data")
def test_clean_added_user_no_refresh(get_bmo_data, repo, config, test_bmo_user_data):
    """Test that updated BMO data has no effect when cleaning without refresh."""
    get_bmo_data.return_value = test_bmo_user_data

    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    assert file_config.config["people"] == config["people"]

    file_config.config["people"].insert(1, {"bmo_id": 3})
    file_config.write()

    assert len(file_config.config["people"]) == 5

    # Check that the new entry is unaffected after write.
    for person in file_config.config["people"]:
        if person["bmo_id"] == 3:
            # Ensure only the bmo_id key is there.
            assert len(person) == 1, "Only the bmo_id key should be present."

    # Compare the old and new people lists without the new entry, they should match.
    new = sorted(
        [
            dict(person)
            for person in file_config.config["people"]
            if person["bmo_id"] != 3
        ],
        key=itemgetter("bmo_id"),
    )
    original = sorted([person for person in config["people"]], key=itemgetter("bmo_id"))
    assert new == original

    # Run clean without refresh.
    clean(file_config, refresh=False)

    # It is expected that only the new entry is updated, and the rest are intact.
    explain_assert_existing = "Existing records should not be updated after clean."
    cleaned = sorted(file_config.config["people"], key=itemgetter("bmo_id"))
    assert len(cleaned) == 5
    assert cleaned[0] == original[0], explain_assert_existing
    assert cleaned[1] == original[1], explain_assert_existing
    assert cleaned[2] == original[2], explain_assert_existing
    assert cleaned[3] == {
        "bmo_id": 3,
        "name": "seven",
        "nick": "nanotubes",
    }, "New entry should have been updated after clean."


@mock.patch("mots.config.get_bmo_data")
def test_clean_added_user_with_refresh(get_bmo_data, repo, config, test_bmo_user_data):
    """Test that updated BMO data is reflected when cleaning with a refresh."""
    get_bmo_data.return_value = test_bmo_user_data

    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    assert file_config.config["people"] == config["people"]

    file_config.config["people"].append({"bmo_id": 3})
    file_config.write()

    assert len(file_config.config["people"]) == 5

    # Check that the new entry is unaffected after write.
    for person in file_config.config["people"]:
        if person["bmo_id"] == 3:
            # Ensure only the bmo_id key is there.
            assert len(person) == 1

    # Compare the old and new people lists without the new entry, they should match.
    new = sorted(
        [
            dict(person)
            for person in file_config.config["people"]
            if person["bmo_id"] != 3
        ],
        key=itemgetter("bmo_id"),
    )
    original = sorted(config["people"], key=itemgetter("bmo_id"))
    assert new == original

    # Run clean with refresh.
    clean(file_config, refresh=True)

    # It is expected that all people will have been updated via BMO.
    explain_assert_all = "Record should have been updated after clean."
    cleaned = sorted(file_config.config["people"], key=itemgetter("bmo_id"))
    assert len(cleaned) == 5
    assert cleaned[0] == {
        "bmo_id": 0,
        "name": "janeway",
        "nick": "captain",
    }, explain_assert_all
    assert cleaned[1] == {
        "bmo_id": 1,
        "name": "tuvok",
        "nick": "2vk",
    }, explain_assert_all
    assert cleaned[2] == {
        "bmo_id": 2,
        "name": "neelix",
        "nick": "cooks4u",
    }, explain_assert_all
    assert cleaned[3] == {
        "bmo_id": 3,
        "name": "seven",
        "nick": "nanotubes",
    }, explain_assert_all
    assert cleaned[4] == {
        "bmo_id": 4,
        "name": "tom paris",
        "nick": "paris",
    }, explain_assert_all
