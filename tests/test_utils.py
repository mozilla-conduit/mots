# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for utils module."""

from unittest.mock import MagicMock

import pytest

from mots.utils import (
    generate_machine_readable_name,
    mkdir_if_not_exists,
    parse_real_name,
    touch_if_not_exists,
)


@pytest.fixture(scope="function")
def mock_path():
    def _mock_path(exists=False, is_dir=False, is_file=False):
        assert exists is True or exists is False
        if not exists:
            assert is_file is False and is_dir is False
        else:
            assert is_file is False or is_dir is False

        path = MagicMock()
        path.exists.return_value = exists
        if exists:
            path.is_dir.return_value = is_dir
            path.is_file.return_value = is_file
        else:
            path.is_dir.return_value = False
            path.is_file.return_value = False
        return path

    return _mock_path


def test_generate_machine_readable_name():
    assert generate_machine_readable_name("Hello, world!") == "hello_world"
    assert generate_machine_readable_name("test") == "test"
    assert generate_machine_readable_name("Another test !@%#@") == "another_test"
    assert generate_machine_readable_name("User Interface (UI)") == "user_interface_ui"
    assert generate_machine_readable_name("test: testing") == "test_testing"


def test_parse_real_name():
    assert parse_real_name("tëstér testerson (:test) [te/st]") == {
        "name": "tëstér testerson",
        "info": "(:test) [te/st]",
    }

    assert parse_real_name("tester testerson [:test] (te/st)") == {
        "name": "tester testerson",
        "info": "[:test] (te/st)",
    }

    assert parse_real_name("tester testerson (te/st)") == {
        "name": "tester testerson",
        "info": "(te/st)",
    }

    assert parse_real_name("tester testerson :test") == {
        "name": "tester testerson",
        "info": ":test",
    }

    # This test is not great, but some folks have their e-mail instead of name.
    assert parse_real_name("tester@testerson.example (:test)") == {
        "name": "tester",
        "info": "@testerson.example (:test)",
    }

    assert parse_real_name("Emoji Tester💡 :tester") == {
        "name": "Emoji Tester",
        "info": "💡 :tester",
    }

    assert parse_real_name("tester testerson | TEST | te/st") == {
        "name": "tester testerson",
        "info": "| TEST | te/st",
    }

    assert parse_real_name("tester testerson") == {
        "name": "tester testerson",
        "info": "",
    }

    assert parse_real_name("tester") == {
        "name": "tester",
        "info": "",
    }

    assert parse_real_name("(:bees)") == {
        "name": "",
        "info": "(:bees)",
    }

    assert parse_real_name("[:bees]") == {
        "name": "",
        "info": "[:bees]",
    }

    assert parse_real_name("[bees]") == {
        "name": "",
        "info": "[bees]",
    }

    assert parse_real_name("(bees)") == {
        "name": "",
        "info": "(bees)",
    }

    assert parse_real_name("") == {
        "name": "",
        "info": "",
    }


def test_mkdir_if_not_exists__does_not_exist(mock_path):
    path = mock_path(exists=False)
    mkdir_if_not_exists(path)
    assert path.exists.call_count == 1
    assert path.mkdir.call_count == 1


def test_mkdir_if_not_exists__exists_as_file(mock_path):
    path = mock_path(exists=True, is_file=True)
    mkdir_if_not_exists(path)
    assert path.exists.call_count == 2
    assert path.mkdir.call_count == 0


def test_mkdir_if_not_exists__exists(mock_path):
    path = mock_path(exists=True, is_dir=True)
    mkdir_if_not_exists(path)
    assert path.exists.call_count == 2
    assert path.mkdir.call_count == 0


def test_touch_if_not_exists__does_not_exist(mock_path):
    path = mock_path(exists=False)
    touch_if_not_exists(path)
    assert path.exists.call_count == 1
    assert path.touch.call_count == 1


def test_touch_if_not_exists__exists_as_dir(mock_path):
    path = mock_path(exists=True, is_dir=True)
    touch_if_not_exists(path)
    assert path.exists.call_count == 2
    assert path.touch.call_count == 0


def test_touch_if_not_exists__exists(mock_path):
    path = mock_path(exists=True, is_file=True)
    touch_if_not_exists(path)
    assert path.exists.call_count == 2
    assert path.touch.call_count == 0
