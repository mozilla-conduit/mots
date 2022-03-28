# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Integration tests for mots.module."""

from mots.config import FileConfig, add, validate
from mots.module import Module


def test_module__Module(repo):
    file_config = FileConfig(repo / "mots.yml")
    file_config.load()
    modules = file_config.config["modules"]

    assert len(modules) == 2
    m = Module(repo_path=repo, **modules[0])

    assert m.machine_name == "domesticated_animals"
    assert len(m.includes) == 5
    assert len(m.excludes) == 1
    assert len(m.submodules) == 1
    assert len(m.owners) == 1

    assert m.submodules[0].machine_name == "predators"
    assert len(m.submodules[0].includes) == 4
    # TODO: should excludes be inherited like this? Might need to revisit this.
    assert len(m.submodules[0].excludes) == 1
    assert len(m.submodules[0].owners) == 1


def test_module__Module__calculate_paths(repo):
    file_config = FileConfig(repo / "mots.yml")
    file_config.load()
    modules = file_config.config["modules"]
    m = Module(repo_path=repo, **modules[0])
    assert len(m.calculate_paths()) == 10
    assert len(m.submodules[0].calculate_paths()) == 3


def test_module__Module__validate(repo):
    m = Module(
        name="Some Module",
        machine_name="some_module",
        repo_path=str(repo),
        includes="*",
    )
    errors = m.validate()
    assert errors == []


def test_module__Module__validate__error_no_paths_in_submodule(repo):
    """Ensure an error is thrown when a submodule contains no valid paths."""
    m = dict(
        name="Some Module",
        machine_name="some_module",
        includes="*",
        submodules=[
            dict(
                name="Submodule",
                machine_name="submodule",
                excludes="*",
            ),
            dict(
                name="Submodule2",
                machine_name="submodule2",
                excludes="*",
            ),
        ],
    )
    m = Module(**m, repo_path=str(repo))
    errors = m.validate()
    assert errors == [
        "No valid paths were found in submodule.",
        "No valid paths were found in submodule2.",
    ]


def test_module__Module__validate__invalid_machine_name(repo):
    """Ensure an error is thrown when a submodule has an invalid machine name."""
    m = dict(
        machine_name="some module",
        includes="*",
    )
    m = Module(**m, repo_path=str(repo))
    errors = m.validate()
    assert errors == ["Machine name some module contains white space."]

    m = dict(
        machine_name="",
        includes="*",
    )
    m = Module(**m, repo_path=str(repo))
    errors = m.validate()
    assert errors == ["Module has a blank machine_name."]


def test_module__Module__serialize(repo):
    assert True


def test_module__validate(repo, config):
    result = validate(config, str(repo))
    assert result is None


def test_module__validate__error_duplicate_machine_names(repo):
    """Ensure an error is thrown when there are duplicate machine names in modules."""
    config = {
        "repo": "test_repo",
        "created_at": "2021-09-10 12:53:22.383393",
        "updated_at": "2021-09-10 12:53:22.383393",
        "modules": [
            {
                "name": "m1",
                "machine_name": "m1",
                "includes": ["*"],
                "submodules": [
                    {
                        "name": "m1",
                        "machine_name": "m1",
                    },
                    {
                        "name": "m3",
                        "machine_name": "m3",
                    },
                ],
            },
            {
                "name": "m2",
                "machine_name": "m2",
                "includes": ["*"],
                "submodules": [
                    {
                        "name": "m3",
                        "machine_name": "m3",
                    },
                ],
            },
        ],
    }

    messages = validate(config, repo)
    assert messages == ["Duplicate machine name(s) found: m1, m3"]


def test_module__validate__error_no_paths(repo):
    """Ensure an error is thrown when there are duplicate machine names in modules."""
    config = {
        "repo": "test_repo",
        "created_at": "2021-09-10 12:53:22.383393",
        "updated_at": "2021-09-10 12:53:22.383393",
        "modules": [
            {
                "name": "m1",
                "machine_name": "m1",
                "includes": ["does_not_exist"],
            },
        ],
    }

    messages = validate(config, repo)
    assert messages == ["No valid paths were found in m1."]


def test_module__add(repo):
    file_config = FileConfig(repo / "mots.yml")
    file_config.load()

    module = {
        "machine_name": "reptiles",
        "includes": ["reptiles/**/*"],
        "owners": [{"nick": "otis", "bmo_id": 2, "info": "testing"}],
    }

    add(module, file_config, parent="pets", write=True)
    file_config.load()
    # NOTE should we be storing machine names as keys in a dict, instead of a list?
    # even an ordered dict? This might make some things a little easier.
    assert (
        file_config.config["modules"][1]["submodules"][0]["machine_name"] == "reptiles"
    )
    assert file_config.config["modules"][1]["submodules"][0]["includes"] == [
        "reptiles/**/*"
    ]
    assert file_config.config["modules"][1]["submodules"][0]["owners"] == [
        {"nick": "otis", "bmo_id": 2, "info": "testing"}
    ]

    # TODO: validate that includes, excludes, and owners are lists...
