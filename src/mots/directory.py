# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Directory classes for mots."""

from __future__ import annotations
from collections import defaultdict
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import InitVar
import logging
from mots.bmo import BMOClient
from mots.module import Module
from mots.config import FileConfig
from mots.utils import parse_real_name

logger = logging.getLogger(__name__)

WIKI_TMPL = """
{% macro people_entry(people) %}
{%- for p in people %}{{ p.nick }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endmacro %}

{%- macro module_entry(module) -%}
{% raw %}{{Module{% endraw %}
|name={{ module.name }}
|description={{ module.description }}
|owner(s)={{ people_entry(module.owners) -}}
|peer(s)={{ people_entry(module.peers) -}}
|includes={{ module.includes|join(", ") }}
|excludes={{ module.excludes|join(", ") }}
{%- if module.meta.group -%}
|group={{ module.meta.group }}
{% endif %}
{%- if module.meta.url -%}
|url={{ module.meta.group }}
{% endif %}
{%- if module.meta.components -%}
|url={{ module.meta.components }}
{% endif %}
{% raw %}}}{% endraw %}
{% endmacro %}


{{ directory.description or "No directory description provided." }}

{%- for module in directory.modules -%}
{{ module_entry(module) }}
{% if module.submodules %}
== Submodules ==
{% for submodule in module.submodules %}
{{ module_entry(submodule) }}
{% endfor %}
{% endif %}
{% endfor %}
"""


class Directory:
    """Mots directory and path index."""

    def __init__(self, config: FileConfig):
        self.config_handle = config
        self.config_handle.load()

        self.repo_path = self.config_handle.repo_path
        self.modules = [
            Module(repo_path=self.repo_path, **m)
            for m in self.config_handle.config["modules"]
        ]

        self.modules_by_machine_name = {}
        for module in self.modules:
            self.modules_by_machine_name[module.machine_name] = module

        self.index = None
        self.people = None

    def load(self, full_paths: bool = False, query_bmo=True):
        """Load all paths in each module and put them in index."""
        self.index = defaultdict(list)

        if full_paths:
            # Make sure all existing paths have an entry in the index.
            logger.debug("Loading paths into index...")
            for path in self.repo_path.glob("**/*"):
                if path.relative_to(self.repo_path).parts[0] in (".hg", ".git"):
                    continue
                self.index[path] = list()
            logger.debug(f"{len(self.index)} paths loaded.")

        for module in self.modules:
            if module.submodules:
                # Start with more specific submodule definitions if present.
                for submodule in module.submodules:
                    logger.debug(f"Updating index for {submodule.machine_name}...")
                    for path in submodule.calculate_paths():
                        self.index[path].append(submodule)
            logger.debug(f"Updating index for {module.machine_name}...")
            # Add broader module definitions.
            for path in module.calculate_paths():
                self.index[path].append(module)

        # Filter out modules that specifically exclude paths defined in other modules.
        for path in self.index.keys():
            modules = self.index[path]
            if len(modules) > 1:
                self.index[path] = [m for m in modules if not m.exclude_module_paths]
        self.index = dict(self.index)

        # Load people directory
        self.people = People(self.config_handle.config["people"], query_bmo=query_bmo)
        if self.people.serialized != list(self.config_handle.config["people"]):
            logger.debug("People directory modified, updating configuration...")
            self.config_handle.config["people"] = self.people.serialized

    def query(self, *paths: str) -> QueryResult:
        """Query given paths and return a list of corresponding modules."""
        result = {}
        rejected = []
        for path in paths:
            if not (self.repo_path / path).exists():
                logger.warning(f"Path {path} does not exist, skipping.")
                rejected.append(path)
                continue
            result[path] = self.index.get(self.repo_path / path, list())
        logger.debug(f"Query {paths} resolved to {result}.")

        return QueryResult(result, rejected)

    def _export_wiki(self):
        from jinja2 import Template

        template = Template(WIKI_TMPL)
        out = template.render(directory=self)
        return out

    def export(self, frmt="wiki"):
        """Export directory in a specified format."""
        supported_formats = ["wiki"]
        if frmt not in supported_formats:
            raise ValueError(f"{frmt} not one of {supported_formats}.")

        return getattr(self, f"_export_{frmt}")()


class QueryResult:
    """Helper class to simplify query result interpretation."""

    paths: list = None
    path_map: dict = None
    rejected_paths: list = None
    modules: list = None
    owners: list = None
    peers: list = None

    data_keys = {
        "paths",
        "rejected_paths",
        "modules",
        "owners",
        "peers",
    }

    def __init__(self, result, rejected):
        data = {k: list() for k in self.data_keys}
        self.path_map = result

        for path in self.path_map:
            data["paths"].append(path)
            data["modules"] += self.path_map[path]

        for module in data["modules"]:
            # TODO: this conversion should happen elsewhere.
            data["owners"] += [Person(**o) for o in module.owners]
            data["peers"] += [Person(**p) for p in module.peers]

        data["rejected_paths"] = rejected

        # Remove duplicate entries in all data attributes.
        for key in data:
            setattr(self, key, list(set(data[key])))

    def __add__(self, query_result):
        """Merge the data from both QueryResult objects."""
        path_map = self.path_map.copy()
        path_map.update(query_result.path_map)
        rejected_paths = set.intersection(
            set(self.rejected_paths),
            set(query_result.rejected_paths),
        )
        return QueryResult(path_map, rejected_paths)

    def __radd__(self, query_result):
        """Call self.__add__ since the order of addition does not matter."""
        return self.__add__(query_result)


@dataclass
class Person:
    """A class representing a person."""

    bmo_id: int = None
    name: str = ""
    info: str = ""
    nick: str = ""
    bmo_data: InitVar[dict] = None

    def __post_init__(self, bmo_data):
        """Refresh BMO data from BMO API."""
        if bmo_data:
            self.nick = bmo_data.get("nick", "")
            self.bmo_id = bmo_data.get("id") or self.bmo_id
            real_name = bmo_data.get("real_name", "")

            parsed_real_name = parse_real_name(real_name)
            self.name = parsed_real_name["name"]
            self.info = parsed_real_name["info"]

    def __hash__(self):
        """Return a unique identifier for this person."""
        return int(self.bmo_id)


class People:
    """A people directory searchable by name, email, or BMO ID."""

    by_bmo_id: dict = None
    people: list = None
    serialized: list = None

    def __init__(self, people, query_bmo: bool = True):
        logger.debug(f"Initializing people directory with {len(people)} people...")
        if query_bmo:
            bmo_client = BMOClient()
            bmo_data = bmo_client.get_users_by_ids([p["bmo_id"] for p in people])
        else:
            bmo_data = {}
        people = list(people)
        self.people = []
        self.by_bmo_id = {}
        for i in range(len(people)):
            p = people[i]
            logger.debug(f"Adding person {p} to roster...")
            self.people.append(
                Person(
                    bmo_id=p["bmo_id"],
                    bmo_data=bmo_data.get(p["bmo_id"]),
                )
            )
            self.by_bmo_id[p["bmo_id"]] = i
            logger.debug(f"Person {p} added to position {i}.")
        self.serialized = [asdict(p) for p in self.people]
