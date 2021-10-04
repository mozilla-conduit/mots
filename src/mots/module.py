# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Module operations and utility functions."""

from __future__ import annotations
from collections import defaultdict
import logging
from pathlib import Path
from mots.utils import generate_machine_readable_name
from mots.config import FileConfig

logger = logging.getLogger(__name__)


class ValidationError(TypeError):
    """Thrown when a particular module is not valid."""

    pass


class Module:
    """A top-level module or a submodule.

    :param machine_name: a unique, machine-readable name for the module
    :param repo_path: the path of the top-level repository
    :param name: the name of the module
    :param includes: a list of paths (glob format) to include
    :param excludes: a list of paths (glob format) to exclude
    :param owners: a list of owners that will own all paths in this module
    :param meta: a dictionary of meta data related to this module
    :param parent: the parent module of this module, if this is a submodule
    :param submodules: a list of submodules of this module
    :param exclude_submodule_paths: when True, paths in submodules are excluded
    :param exclude_module_paths: when True, common paths in other modules are excluded
        from the directory index
    """

    def __repr__(self):
        """Return a human readable name for the instance."""
        return f"<Module: {self.machine_name}>"

    def __init__(
        self,
        machine_name: str,
        repo_path: str,
        name: str = None,
        includes: str = None,
        excludes: str = None,
        owners: list[str] = None,
        meta: dict = None,
        parent: "Module" = None,
        submodules: list[dict] = None,
        exclude_submodule_paths: bool = True,
        exclude_module_paths: bool = False,
    ):
        self.name = name
        self.machine_name = machine_name
        self.repo_path = Path(repo_path)
        self.parent = parent

        self.excludes = excludes or []
        self.includes = includes or []
        self.owners = owners or []
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

    def calculate_paths(self):
        """Calculate paths based on inclusions and exclusions.

        Upon calling this method, excluded paths are parsed using `pathlib.Path.rglob`
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

    def validate(self, errors=None):
        """Perform validation on module and submodules recursively.

        Starting with the current module, ensure that this module includes at least one
        valid path and a valid name and machine name,  and then run the same validation
        on all submodules.

        :param errors: a list of errors to append to
        :rtype: list
        """
        errors = errors or []

        if not self.machine_name.strip():
            errors.append("Module has a blank machine_name.")

        if " " in self.machine_name:
            errors.append(f"Machine name {self.machine_name} contains white space.")

        if not self.calculate_paths():
            errors.append(f"No valid paths were found in {self.machine_name}.")

        # TODO validate owners

        if self.submodules:
            for submodule in self.submodules:
                return submodule.validate(errors=errors)

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
    modules_by_name = {}
    for _module in modules:
        modules_by_name[_module["machine_name"]] = _module
    if module not in modules_by_name:
        raise ValueError(f"{module} not found.")
    else:
        print(modules_by_name[module])


def clean(file_config: FileConfig, write: bool = True):
    """Clean and re-sort configuration file.

    Load condiguration from disk, sort modules and submodules by `machine_name`. If
    there is no valid `machine_name`, generate one. Write changes to disk.

    :param file_config: an instance of :class:`FileConfig`
    :param bool: if set to `True`, writes changes to disk.
    """
    file_config.load()
    file_config.config["modules"].sort(key=lambda x: x["machine_name"])
    for i in range(len(file_config.config["modules"])):
        module = file_config.config["modules"][i]
        if "machine_name" not in module:
            module["machine_name"] = generate_machine_readable_name(module["name"])
        if "submodules" in module and module["submodules"]:
            module["submodules"].sort(key=lambda x: x["name"])
            for submodule in module["submodules"]:
                if "machine_name" not in submodule:
                    submodule["machine_name"] = generate_machine_readable_name(
                        submodule["name"]
                    )
    if write:
        file_config.write()


def validate(config: dict, repo_path: str):
    """Validate the current state of the config file.

    - Check if top-level dictionary contains required keys
    - Check if machine names are unique
    - Instantiate and run validation on each :class:`Module` instance

    :raises ValidationError: if any validation errors are detected
    """
    # Validate that config has all the required keys.
    required_keys = ("repo", "created_at", "updated_at", "modules")
    keys_diff = required_keys - config.keys()
    if len(keys_diff) != 0:
        raise ValidationError(f"{keys_diff} missing from configuration file.")

    modules = config["modules"]

    # Count machine name repetitions in a defaultdict.
    machine_names = defaultdict(int)
    for m in modules:
        machine_names[m["machine_name"]] += 1
        if "submodules" in m and m["submodules"]:
            for sm in m["submodules"]:
                machine_names[sm["machine_name"]] += 1

    machine_names = {name: count for name, count in machine_names.items() if count > 1}
    if machine_names:
        raise ValidationError(
            f"Duplicate machine name(s) found: {', '.join(machine_names.keys())}"
        )

    errors = []
    for i in range(len(config["modules"])):
        module = config["modules"][i]
        module = Module(repo_path=repo_path, **module)
        validation_errors = module.validate()
        if validation_errors:
            errors.append(validation_errors)

    if errors:
        raise ValidationError(errors)
    logger.info("All modules validated successfully.")
