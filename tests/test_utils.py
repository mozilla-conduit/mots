# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for utils module."""

from mots.utils import generate_machine_readable_name


def test_generate_machine_readable_name():
    assert generate_machine_readable_name("Hello, world!") == "hello_world"
    assert generate_machine_readable_name("test") == "test"
    assert generate_machine_readable_name("Another test !@%#@") == "another_test"
    assert generate_machine_readable_name("User Interface (UI)") == "user_interface_ui"
    assert generate_machine_readable_name("test: testing") == "test_testing"
