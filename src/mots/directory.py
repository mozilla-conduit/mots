# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Directory classes for mots."""

from __future__ import annotations
from collections import defaultdict
from dataclasses import asdict
from dataclasses import dataclass
import logging
from mots.module import Module
from mots.utils import parse_real_name

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mots.config import FileConfig


logger = logging.getLogger(__name__)


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
        people = list(self.config_handle.config["people"])
        self.people = People(people, {})

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


class QueryResult:
    """Helper class to simplify query result interpretation."""

    data_keys = {
        "paths",
        "rejected_paths",
        "modules",
        "owners",
        "peers",
    }

    def __init__(self, result, rejected):
        data = {k: set() for k in self.data_keys}
        self.path_map = result

        for path in self.path_map:
            data["paths"].add(path)
            data["modules"].update(self.path_map[path])

        for module in data["modules"]:
            data["owners"].update([Person(**o) for o in module.owners])
            data["peers"].update([Person(**p) for p in module.peers])

        data["rejected_paths"].update(rejected)

        for key in data:
            setattr(self, key, list(data[key]))

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

    bmo_id: int
    name: str
    info: str
    nick: str

    def __hash__(self):
        """Return a unique identifier for this person."""
        return self.bmo_id


class People:
    """A people directory searchable by name, email, or BMO ID."""

    def __init__(self, people, bmo_data: dict):
        logger.debug(f"Initializing people directory with {len(people)} people...")

        self.people = []
        self.by_bmo_id = {}

        people = list(people)
        for i, person in enumerate(people):
            logger.debug(f"Adding person {person} to roster...")

            bmo_id = person["bmo_id"] = int(person["bmo_id"])
            if bmo_id in bmo_data and bmo_data[bmo_id]:
                # Update person's data base on BMO data.
                bmo_datum = bmo_data[person["bmo_id"]]
                person["nick"] = bmo_datum.get("nick", "")

                parsed_real_name = parse_real_name(bmo_datum["real_name"])
                person["name"] = parsed_real_name["name"]
                person["info"] = parsed_real_name["info"]

            self.people.append(Person(**person))
            self.by_bmo_id[person["bmo_id"]] = i
            logger.debug(f"Person {person} added to position {i}.")
        self.serialized = [asdict(person) for person in self.people]

    def refresh_by_bmo_id(self):
        """Refresh index positions of people by their bugzilla ID."""
        self.by_bmo_id = {}
        for i, person in enumerate(self.people):
            self.by_bmo_id[person.bmo_id] = i
