# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for utils module."""

from mots.utils import (
    generate_machine_readable_name,
    parse_real_name,
)


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

    assert parse_real_name("tester testerson | TEST | te/st") == {
        "name": "tester testerson",
        "info": "| TEST | te/st",
    }

    assert parse_real_name("tester testerson") == {
        "name": "tester testerson",
        "info": None,
    }

    assert parse_real_name("tester") == {
        "name": "tester",
        "info": None,
    }

    assert parse_real_name("(:bees)") == {
        "name": None,
        "info": "(:bees)",
    }

    assert parse_real_name("[:bees]") == {
        "name": None,
        "info": "[:bees]",
    }

    assert parse_real_name("[bees]") == {
        "name": None,
        "info": "[bees]",
    }

    assert parse_real_name("(bees)") == {
        "name": None,
        "info": "(bees)",
    }

    assert parse_real_name("") == {
        "name": None,
        "info": None,
    }
