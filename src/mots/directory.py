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
        self.people = People(self.config_handle.config["people"], query_bmo=query_bmo)
        if self.people.serialized != list(self.config_handle.config["people"]):
            logger.debug("People directory modified, updating configuration...")
            self.config_handle.config["people"] = self.people.serialized

    def query(self, *paths: str) -> tuple[list[Module], list[str]]:
        """Query given paths and return a list of corresponding modules."""
        result = {}
        rejected = []
        for path in paths:
            if not (self.repo_path / path).exists():
                logger.warning(f"Path {path} does not exist, skipping.")
                rejected.append(path)
                continue
            result[path] = self.index.get(self.repo_path / path, list())
        logger.info(f"Query {paths} resolved to {result}.")

        # NOTE: for new files, we need to use the old config against the new file
        # structure.
        return result, rejected


@dataclass
class Person:
    """A class representing a person."""

    bmo_id: int = None
    real_name: str = ""
    nick: str = ""
    bmo_data: InitVar[dict] = None

    def __post_init__(self, bmo_data):
        """Refresh BMO data from BMO API."""
        if bmo_data:
            self.nick = bmo_data.get("nick", "")
            self.real_name = bmo_data.get("real_name", "")


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
                    real_name=p["real_name"],
                    bmo_id=p["bmo_id"],
                    bmo_data=bmo_data.get(p["bmo_id"]),
                )
            )
            self.by_bmo_id[p["bmo_id"]] = i
            logger.debug(f"Person {p} added to position {i}.")
        self.serialized = [asdict(p) for p in self.people]
