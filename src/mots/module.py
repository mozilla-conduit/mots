# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Module operations and utility functions."""

from __future__ import annotations

import logging
from pathlib import Path
from pprint import pprint as print

logger = logging.getLogger(__name__)


class Module:
    """A top-level module or a submodule.

    :param machine_name: a unique, machine-readable name for the module
    :param repo_path: the path of the top-level repository
    :param name: the name of the module
    :param description: the description of the module
    :param includes: a list of paths (glob format) to include
    :param excludes: a list of paths (glob format) to exclude
    :param owners: a list of owners that will own all paths in this module
    :param peers: a list of peers for this module
    :param meta: a dictionary of meta data related to this module
    :param parent: the parent module of this module, if this is a submodule
    :param submodules: a list of submodules of this module
    :param exclude_submodule_paths: when True, paths in submodules are excluded
    :param exclude_module_paths: when True, common paths in other modules are excluded
        from the directory index

    The ``Module`` class wraps modules and submodules in a configuration, and provides
    useful methods for validation, calculating paths, and serialization.
    """

    def __repr__(self):
        """Return a human readable name for the instance."""
        return f"<Module: {self.machine_name}>"

    def __init__(
        self,
        machine_name: str,
        repo_path: str | Path,
        name: str = "",
        description: str = "",
        includes: list[str] | None = None,
        excludes: list[str] | None = None,
        owners: list[dict] | None = None,
        peers: list[dict] | None = None,
        meta: dict = None,
        parent: "Module" = None,
        submodules: list[dict] | None = None,
        exclude_submodule_paths: bool = True,
        exclude_module_paths: bool = False,
    ):
        self.name = name
        self.machine_name = machine_name
        self.description = description
        self.repo_path = Path(repo_path)
        self.parent = parent

        self.excludes = excludes or []
        self.includes = includes or []
        self.owners = owners or []
        self.peers = peers or []
        self.submodules = []
        self.exclude_submodule_paths = exclude_submodule_paths
        self.exclude_module_paths = exclude_module_paths
        self.errors = []

        if submodules:
            for module in submodules:
                self.submodules.append(
                    Module(parent=self, repo_path=repo_path, **module)
                )

        self.meta = meta

        # `includes`, `excludes`, and `owners` can be omitted in submodules, in which
        # case they will be inherited from their parent module.
        if not self.includes and self.parent:
            self.includes = self.parent.includes

        if not self.excludes and self.parent:
            self.excludes = self.parent.excludes

        if not self.owners and self.parent:
            self.owners = self.parent.owners

        if not self.peers and self.parent:
            self.peers = self.parent.peers

        self.owner_names = [owner.get("nick", "") for owner in self.owners]
        self.peer_names = [peer.get("nick", "") for peer in self.peers]

    def calculate_paths(self):
        """Calculate paths based on inclusions and exclusions.

        Upon calling this method, excluded paths are parsed using ``pathlib.Path.rglob``
        and then subtracted from the included paths, which are parsed in the same way.

        :rtype: set
        """
        includes = []
        for pattern in self.includes:
            logger.debug(f"Expanding {pattern} in {self.machine_name}...")
            expanded = list(self.repo_path.glob(pattern))
            logger.debug(
                f"Pattern {pattern} expanded to {len(expanded)} included path(s)."
            )
            includes += expanded

        excludes = []
        for pattern in self.excludes:
            logger.debug(f"Expanding {pattern} in {self.machine_name}...")
            expanded = list(self.repo_path.glob(pattern))
            logger.debug(
                f"Pattern {pattern} expanded to {len(expanded)} excluded path(s)."
            )
            excludes += expanded

        paths = set(includes) - set(excludes)
        if self.exclude_submodule_paths:
            for submodule in self.submodules:
                paths -= submodule.calculate_paths()
        return paths

    def serialize(self):
        """Return a dictionary with relevant module information.

        :rtype: dict
        """
        serialized = {
            "machine_name": self.machine_name,
            "name": self.name,
            "description": self.description,
            "includes": self.includes,
            "excludes": self.excludes,
            "owners": self.owners,
            "peers": self.peers,
            "meta": self.meta,
        }

        if self.submodules:
            serialized["submodules"] = [sm.serialize() for sm in self.submodules]
        if self.parent:
            serialized["parent"] = self.parent.machine_name

        return serialized

    def validate(self):
        """Perform validation on module and submodules recursively.

        Starting with the current module, ensure that this module includes at least one
        valid path and a valid name and machine name,  and then run the same validation
        on all submodules.

        :param errors: a list of errors to append to
        :rtype: list
        """
        errors = []

        if not self.machine_name.strip():
            errors.append("Module has a blank machine_name.")

        if " " in self.machine_name:
            errors.append(f"Machine name {self.machine_name} contains white space.")

        if not self.calculate_paths():
            errors.append(f"No valid paths were found in {self.machine_name}.")

        if self.submodules:
            for submodule in self.submodules:
                errors += submodule.validate()

        return errors


def ls(modules: list[Module]):
    """Print a list of given modules.

    :param modules: a list of :class:`Module` instances
    """
    print(modules)


def show(modules: list[Module], module: str):
    """Show details for a particular module.

    :param modules: a list of :class:`Module` instances
    :param module: the `machine_name` of a given :class:`Module`

    :raises ValueError: when no module matches the given machine name
    """
    for _module in modules:
        if _module["machine_name"] == module:
            print(_module)
            return
    raise ValueError(f"{module} not found.")
