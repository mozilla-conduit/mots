# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Export directory to various formats."""

from __future__ import annotations
import logging

import sys

if sys.version_info < (3, 9):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

import jinja2

from mots.directory import Directory

logger = logging.getLogger(__name__)


class Exporter:
    """A helper class that exports to various formats."""

    def __init__(self, directory: Directory):
        self.directory = directory

    def _export_to_rst(self):
        loader = jinja2.FileSystemLoader(
            searchpath=importlib_resources.files("mots") / "templates"
        )
        env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
        template = env.get_template("directory.template.rst")
        out = template.render(directory=self.directory)
        return out


def export_to_format(directory: Directory, frmt="rst"):
    """Export directory in a specified format."""
    supported_formats = ["rst"]
    if frmt not in supported_formats:
        raise ValueError(f"{frmt} not one of {supported_formats}.")

    exporter = Exporter(directory)
    return getattr(exporter, f"_export_to_{frmt}")()
