# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for directory module."""

from mots.directory import Directory, Person, QueryResult
from mots.module import Module
from mots.config import FileConfig


def test_directory__Directory(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    directory.load(full_paths=True)

    rp = directory.repo_path
    di = directory.index

    assert len(di) == 24

    assert [m.machine_name for m in di[rp / "birds"]] == []
    assert [m.machine_name for m in di[rp / "birds/eagle"]] == ["predators"]
    assert [m.machine_name for m in di[rp / "birds/parrot"]] == ["pets"]
    assert [m.machine_name for m in di[rp / "bovines"]] == []
    assert [m.machine_name for m in di[rp / "bovines/cow"]] == ["domesticated_animals"]
    assert [m.machine_name for m in di[rp / "bovines/sheep"]] == [
        "domesticated_animals"
    ]
    assert [m.machine_name for m in di[rp / "canines"]] == []
    assert [m.machine_name for m in di[rp / "canines/beagle"]] == ["pets"]
    assert [m.machine_name for m in di[rp / "canines/chihuahuas"]] == ["pets"]
    assert [m.machine_name for m in di[rp / "canines/chihuahuas/apple_head"]] == [
        "pets"
    ]
    assert [m.machine_name for m in di[rp / "canines/corgy"]] == ["pets"]
    assert [m.machine_name for m in di[rp / "canines/hyena"]] == ["predators"]
    assert [m.machine_name for m in di[rp / "canines/red_fox"]] == []
    assert [m.machine_name for m in di[rp / "felines"]] == []
    assert [m.machine_name for m in di[rp / "felines/cheetah"]] == ["predators"]
    assert [m.machine_name for m in di[rp / "felines/persian"]] == ["pets"]
    assert [m.machine_name for m in di[rp / "marsupials"]] == []
    assert [m.machine_name for m in di[rp / "marsupials/kangaroo"]] == []
    assert [m.machine_name for m in di[rp / "marsupials/koala"]] == []
    assert [m.machine_name for m in di[rp / "mots.yml"]] == []
    assert [m.machine_name for m in di[rp / "pigs"]] == []
    assert [m.machine_name for m in di[rp / "pigs/miniature_pig"]] == [
        "domesticated_animals"
    ]
    assert [m.machine_name for m in di[rp / "pigs/wild_boar"]] == [
        "domesticated_animals"
    ]


def test_directory__Directory_new_path(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    directory.load()
    new_file_path = directory.repo_path / "canines/chihuahuas/deer_head"
    new_file_path.touch()
    assert new_file_path not in directory.index
    directory.load()
    assert new_file_path in directory.index
    assert len(directory.index[new_file_path]) == 1
    assert directory.index[new_file_path][0].machine_name == "pets"


def test_directory__Directory_deleted_path(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    directory.load()
    existing_path = directory.repo_path / "canines/chihuahuas/apple_head"
    assert len(directory.index[existing_path]) == 1
    assert directory.index[existing_path][0].machine_name == "pets"
    assert existing_path in directory.index
    existing_path.unlink()
    directory.load()
    assert existing_path not in directory.index


def test_directory__Directory__query(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    directory.load()

    paths_to_check = [
        "canines/chihuahuas/apple_head",
        "birds/parrot",
        "felines/persian",
        "felines/maine_coon",
    ]

    result = directory.query(*paths_to_check)
    assert result.path_map == {
        "canines/chihuahuas/apple_head": [directory.modules_by_machine_name["pets"]],
        "birds/parrot": [directory.modules_by_machine_name["pets"]],
        "felines/persian": [directory.modules_by_machine_name["pets"]],
    }
    assert set(result.paths) == {
        "canines/chihuahuas/apple_head",
        "birds/parrot",
        "felines/persian",
    }
    assert set(result.owners) == {Person(bmo_id=2, name="otis", nick="otis")}
    assert set(result.peers) == {Person(bmo_id=1, name="jill", nick="jill")}
    assert result.rejected_paths == ["felines/maine_coon"]


def test_directory__Directory__query_merging(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    directory.load()

    paths_to_check_1 = [
        "canines/chihuahuas/apple_head",
        "birds/parrot",
        "felines/maine_coon",
    ]
    paths_to_check_2 = [
        "felines/persian",
        "felines/maine_coon",
    ]

    result_1 = directory.query(*paths_to_check_1)
    result_2 = directory.query(*paths_to_check_2)

    result = result_1 + result_2

    assert result.path_map == {
        "canines/chihuahuas/apple_head": [directory.modules_by_machine_name["pets"]],
        "birds/parrot": [directory.modules_by_machine_name["pets"]],
        "felines/persian": [directory.modules_by_machine_name["pets"]],
    }
    assert set(result.paths) == {
        "canines/chihuahuas/apple_head",
        "birds/parrot",
        "felines/persian",
    }
    assert set(result.owners) == {Person(bmo_id=2, name="otis", nick="otis")}
    assert set(result.peers) == {Person(bmo_id=1, name="jill", nick="jill")}
    assert result.rejected_paths == ["felines/maine_coon"]


def test_directory__Directory__query_add_to_empty_QueryResult(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    directory.load()

    paths_to_check_1 = [
        "canines/chihuahuas/apple_head",
        "birds/parrot",
        "felines/maine_coon",
    ]

    result_1 = directory.query(*paths_to_check_1)

    result = result_1 + QueryResult()

    assert result.path_map == {
        "canines/chihuahuas/apple_head": [directory.modules_by_machine_name["pets"]],
        "birds/parrot": [directory.modules_by_machine_name["pets"]],
    }
    assert set(result.paths) == {
        "canines/chihuahuas/apple_head",
        "birds/parrot",
    }
    assert set(result.owners) == {Person(bmo_id=2, name="otis", nick="otis")}
    assert set(result.peers) == {Person(bmo_id=1, name="jill", nick="jill")}
    assert result.rejected_paths == ["felines/maine_coon"]


def test_directory__QueryResult_empty():
    empty_result = QueryResult()
    assert not empty_result


def test_directory__QueryResult_nonempty():
    test_module = Module(machine_name="test_module", repo_path="/repos/test")
    empty_result = QueryResult({"test_path": [test_module]}, ["rejected_path"])
    assert empty_result


def test_directory__QueryResult_empty_addition():
    empty_result = QueryResult()
    other_empty_result = QueryResult()
    assert not (empty_result + other_empty_result)


def test_directory__peers_and_owners(repo):
    file_config = FileConfig(repo / "mots.yml")
    directory = Directory(file_config)
    assert directory.peers_and_owners == [0, 1, 2]
