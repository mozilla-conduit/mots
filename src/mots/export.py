# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Export directory to various formats."""

import logging

import sys

if sys.version_info < (3, 9):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

import jinja2

from mots.directory import Directory

logger = logging.getLogger(__name__)


def escape_for_rst(value: str) -> str:
    """Escape rst special characters."""
    # First we must escape backslashes, then everything else.
    characters = ("\\", "*", "`")
    for character in characters:
        value = value.replace(character, f"\\{character}")
    return value


class Exporter:
    """A helper class that exports to various formats."""

    @staticmethod
    def _get_env() -> jinja2.Environment:
        """Return a Jinja2 environment preloaded with a FileSystemLoader."""
        loader = jinja2.FileSystemLoader(
            searchpath=importlib_resources.files("mots") / "templates"
        )
        env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
        env.filters["escape_for_rst"] = escape_for_rst
        return env

    def __init__(self, directory: Directory):
        self.directory = directory
        self.env = self._get_env()

    def _get_template(self, frmt: str) -> jinja2.Template:
        """Get a template based on the provided format."""
        template = self.env.get_template(f"directory.template.{frmt}")
        return template

    def _export_to_rst(self) -> str:
        template = self._get_template("rst")
        out = template.render(directory=self.directory)
        return out


def export_to_format(directory: Directory, frmt="rst"):
    """Export directory in a specified format."""
    supported_formats = ["rst"]
    if frmt not in supported_formats:
        raise ValueError(f"{frmt} not one of {supported_formats}.")

    exporter = Exporter(directory)
    return getattr(exporter, f"_export_to_{frmt}")()
