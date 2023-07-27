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
from mots.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_LIST_TABLE_INDENT = 8


def escape_for_rst(value: str) -> str:
    """Escape rst special characters."""
    # First we must escape backslashes, then everything else.
    characters = ("\\", "*", "`")
    for character in characters:
        value = value.replace(character, f"\\{character}")
    return value


def escape_for_md(value: str) -> str:
    """Escape rst special characters."""
    # First we must escape backslashes, then everything else.
    characters = "\\`*_{}[]<>()#+-.!|"
    for character in characters:
        value = value.replace(character, f"\\{character}")
    return value


def format_link_for_rst(text: str, url: str) -> str:
    """Format a link."""
    return f"`{text} <{url}>`__"


def format_link_for_md(text: str, url: str) -> str:
    """Format a link."""
    return f"[{text}]({url})"


def format_paths_for_rst(
    value: list[str], indent: int, directory: Directory = None
) -> str:
    """Escape and format a path string (e.g. for includes or excludes)."""
    config = directory.config_handle.config
    try:
        searchfox_enabled = config["export"]["searchfox_enabled"]
    except KeyError:
        searchfox_enabled = False

    parsed_paths = []
    for path in value:
        path = path.replace("*", "\\*")
        if searchfox_enabled:
            path = format_link_for_rst(
                path,
                f"{settings.SEARCHFOX_BASE_URL}/{config['repo']}/search?q=&path={path}",
            )
        parsed_paths.append(path)
    return f"\n{' ' * indent}| " + f"\n{' ' * indent}| ".join(parsed_paths)


def format_paths_for_md(
    value: list[str], indent: int, directory: Directory = None
) -> str:
    """Escape and format a path string (e.g. for includes or excludes)."""
    config = directory.config_handle.config
    try:
        searchfox_enabled = config["export"]["searchfox_enabled"]
    except KeyError:
        searchfox_enabled = False

    parsed_paths = []
    for path in value:
        path = path.replace("*", "\\*")
        if searchfox_enabled:
            path = format_link_for_md(
                path,
                f"{settings.SEARCHFOX_BASE_URL}/{config['repo']}/search?q=&path={path}",
            )
        parsed_paths.append(path)
    return f"\n{' ' * indent}* " + f"\n{' ' * indent}* ".join(parsed_paths)


def format_people_for_rst(value: list[dict], indent: int) -> str:
    """Escape and format a list of people."""
    people_base_url = settings.PMO_SEARCH_URL
    parsed_people = []
    for person in value:
        url = f"{people_base_url}{person['nick']}"
        if "name" in person and person["name"]:
            parsed_person = format_link_for_rst(
                f"{person['name']} ({person['nick']})", url
            )
        else:
            parsed_person = format_link_for_rst(person["nick"], url)

        parsed_people.append(parsed_person)
    return f"\n{' ' * indent}| " + f"\n{' ' * indent}| ".join(parsed_people)


def format_people_for_md(value: list[dict], indent: int) -> str:
    """Escape and format a list of people."""
    people_base_url = settings.PMO_SEARCH_URL
    parsed_people = []
    for person in value:
        url = f"{people_base_url}{person['nick']}"
        if "name" in person and person["name"]:
            parsed_person = format_link_for_md(
                f"{person['name']} ({person['nick']})", url
            )
        else:
            parsed_person = format_link_for_md(person["nick"], url)

        parsed_people.append(parsed_person)
    return f"\n{' ' * indent}* " + f"\n{' ' * indent}* ".join(parsed_people)


def format_emeritus(value: list[dict | str]) -> str:
    """Return names of people if provided a mixed list."""
    parsed = []
    for person in value:
        if isinstance(person, str):
            parsed.append(person)
        elif isinstance(person, dict):
            if "name" in person and person["name"]:
                parsed.append(person["name"])
            elif "nick" in person and person["nick"]:
                parsed.append(person["nick"])
    return ", ".join(parsed)


def format_review_group_for_rst(group: str) -> str:
    """Format a review group."""
    base_url = settings.PHABRICATOR_BASE_URL
    return format_link_for_rst(f"#{group}", f"{base_url}/tag/{group}/")


def format_review_group_for_md(group: str) -> str:
    """Format a review group."""
    base_url = settings.PHABRICATOR_BASE_URL
    return format_link_for_md(f"#{group}", f"{base_url}/tag/{group}/")


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
        env.filters["format_paths_for_rst"] = format_paths_for_rst
        env.filters["format_people_for_rst"] = format_people_for_rst
        env.filters["format_review_group_for_rst"] = format_review_group_for_rst
        env.filters["escape_for_md"] = escape_for_md
        env.filters["format_paths_for_md"] = format_paths_for_md
        env.filters["format_people_for_md"] = format_people_for_md
        env.filters["format_review_group_for_md"] = format_review_group_for_md
        env.filters["format_emeritus"] = format_emeritus
        return env

    def __init__(self, directory: Directory):
        self.directory = directory
        self.env = self._get_env()

    def _get_template(self, frmt: str) -> jinja2.Template:
        """Get a template based on the provided format."""
        template = self.env.get_template(f"directory.template.{frmt}")
        return template

    def _export_to_rst(self) -> str:
        """Render the template with this instance's directory context and return it."""
        template = self._get_template("rst")
        out = template.render(directory=self.directory)
        return f"{out.strip()}\n"

    def _export_to_md(self) -> str:
        """Render the template with this instance's directory context and return it."""
        template = self._get_template("md")
        out = template.render(directory=self.directory)
        return f"{out.strip()}\n"


def export_to_format(directory: Directory, frmt="rst"):
    """Export directory in a specified format."""
    supported_formats = ["rst", "md"]
    if frmt not in supported_formats:
        raise ValueError(f"{frmt} not one of {supported_formats}.")

    exporter = Exporter(directory)
    return getattr(exporter, f"_export_to_{frmt}")()
