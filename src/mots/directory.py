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
from mots.utils import parse_real_name

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mots.config import FileConfig


logger = logging.getLogger(__name__)


def _get_bmo_data(people: list) -> dict:
    """Fetch an updated dictionary from Bugzilla with user data.

    Dictionary keys are set to user IDs, and values are set to various data.
    """
    bmo_client = BMOClient()
    bmo_data = bmo_client.get_users_by_ids([p["bmo_id"] for p in people])
    return bmo_data


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
        bmo_data = _get_bmo_data(people) if query_bmo else {}
        self.people = People(people, bmo_data)
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
    name: str = ""
    info: str = ""
    nick: str = ""
    bmo_data: InitVar[dict] = None

    def __post_init__(self, bmo_data):
        """Refresh BMO data from BMO API."""
        if bmo_data:
            self.nick = bmo_data.get("nick", "")
            self.bmo_id = bmo_data.get("id", self.bmo_id)
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

    def refresh_by_bmo_id(self):
        """Refresh index positions of people by their bugzilla ID."""
        self.by_bmo_id = {}
        for i, person in enumerate(self.people):
            self.by_bmo_id[person["bmo_id"]] = i

    def __init__(self, people, bmo_data: dict):
        logger.debug(f"Initializing people directory with {len(people)} people...")
        people = list(people)
        self.people = []
        self.by_bmo_id = {}
        for i, person in enumerate(people):
            logger.debug(f"Adding person {person} to roster...")
            # TODO: should have a fallback here without BMO data.
            self.people.append(
                Person(
                    bmo_id=person["bmo_id"],
                    bmo_data=bmo_data.get(person["bmo_id"]),
                )
            )
            self.by_bmo_id[person["bmo_id"]] = i
            logger.debug(f"Person {person} added to position {i}.")
        self.serialized = [asdict(person) for person in self.people]
