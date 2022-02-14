# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Configuration classes used to initialize and manage mots in a repo."""

from collections import defaultdict
import logging

from datetime import datetime
from pathlib import Path
from ruamel.yaml import YAML

from mots.bmo import get_bmo_data
from mots.directory import Directory, People
from mots.module import Module
from mots.utils import generate_machine_readable_name

logger = logging.getLogger(__name__)

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

DEFAULT_CONFIG_FILEPATH = Path("./mots.yaml")


class ValidationError(TypeError):
    """Thrown when a particular module is not valid."""

    pass


class FileConfig:
    """Loader and writer for filesystem based configuration."""

    def __init__(self, path: Path = DEFAULT_CONFIG_FILEPATH):
        """Initialize the configuration with provided config file path."""
        if not path.exists() and path.is_file():
            raise ValueError(f"{path} does not exist or is not a file.")
        self.path = path
        self.repo_path = path.parent
        self.config = None

    def init(self):
        """Initialize a repo with a config file, if it does not contain it."""
        if not self.path.is_file():
            # File does not exist, create it.
            now = datetime.now().isoformat()
            self.config = {
                "repo": str(Path(self.path).resolve().parent.name),
                "created_at": now,
                "updated_at": None,
                "people": [],
                "modules": [],
            }
            self.write()
            logger.info(f"mots configuration initialized in {self.path}.")
        else:
            logger.warning(f"mots configuration file detected in {self.path}.")

    def load(self):
        """Load configuration from file."""
        with self.path.open("r") as f:
            self.config = yaml.load(f)

    def write(self):
        """Write configuration to file, and update the timestamp."""
        self.config["updated_at"] = datetime.now().isoformat()
        with self.path.open("w") as f:
            yaml.dump(self.config, f)


def clean(file_config: FileConfig, write: bool = True):
    """Clean and re-sort configuration file.

    Load configuration from disk, sort modules and submodules by `machine_name`. If
    there is no valid `machine_name`, generate one. Write changes to disk.

    :param file_config: an instance of :class:`FileConfig`
    :param write: if set to `True`, writes changes to disk.
    """
    people_keys = ("owners", "peers")
    file_config.load()
    directory = Directory(file_config)
    directory.load()

    people = list(file_config.config["people"])

    bmo_data = get_bmo_data(people)
    updated_people = People(people, bmo_data)
    logger.debug("Updating people configuration based on BMO data...")
    file_config.config["people"] = updated_people.serialized

    for i, module in enumerate(file_config.config["modules"]):
        if "machine_name" not in module:
            module["machine_name"] = generate_machine_readable_name(module["name"])

        for key in people_keys:
            if key not in module or not module[key]:
                continue
            for i, person in enumerate(module[key]):
                if person["bmo_id"] not in directory.people.by_bmo_id:
                    file_config.config["people"].append(person)
                    module[key][i] = person
                    directory.people.refresh_by_bmo_id()
                else:
                    module[key][i] = file_config.config["people"][
                        directory.people.by_bmo_id[person["bmo_id"]]
                    ]

        # Do the same for submodules.
        if "submodules" in module and module["submodules"]:
            module["submodules"].sort(key=lambda x: x["name"])
            for submodule in module["submodules"]:
                for key in people_keys:
                    if key not in submodule or not submodule[key]:
                        continue
                    for i, person in enumerate(submodule[key]):
                        if person["bmo_id"] not in directory.people.by_bmo_id:
                            file_config.config["people"].append(person)
                            submodule[key][i] = person
                            directory.people.refresh_by_bmo_id()
                        else:
                            submodule[key][i] = file_config.config["people"][
                                directory.people.by_bmo_id[person["bmo_id"]]
                            ]
                if "machine_name" not in submodule:
                    submodule["machine_name"] = generate_machine_readable_name(
                        submodule["name"]
                    )

    file_config.config["modules"].sort(key=lambda x: x["machine_name"])
    if write:
        # Write all changes.
        file_config.write()

        # Reload changes from disk so we can reset all anchors.
        file_config.load()

        nicks = []
        for person in file_config.config["people"]:
            machine_readable_nick = generate_machine_readable_name(
                person.get("nick", ""), keep_case=True
            )
            if machine_readable_nick in nicks or not machine_readable_nick:
                continue
            nicks.append(machine_readable_nick)
            person.yaml_set_anchor(machine_readable_nick)

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
    for module in modules:
        machine_names[module["machine_name"]] += 1
        if "submodules" in module and module["submodules"]:
            for submodule in module["submodules"]:
                machine_names[submodule["machine_name"]] += 1

    machine_names = {name: count for name, count in machine_names.items() if count > 1}
    if machine_names:
        raise ValidationError(
            f"Duplicate machine name(s) found: {', '.join(machine_names.keys())}"
        )

    errors = []
    for i, module in enumerate(config["modules"]):
        module = Module(repo_path=repo_path, **module)
        validation_errors = module.validate()
        if validation_errors:
            errors.append(validation_errors)

    if errors:
        raise ValidationError(errors)
    logger.info("All modules validated successfully.")


def add(
    new_module: dict, file_config: FileConfig, parent: str = None, write: bool = True
):
    """Add a new module to the configuration.

    :param module: a dictionary containing module parameters
    :param file_config: an instance of :class:`FileConfig`
    :param parent: the machine name of the parent module if applicable
    :param write: if set to `True`, writes changes to disk
    """
    file_config.load()
    modules = file_config.config["modules"]
    serialized = Module(**new_module, repo_path=file_config.repo_path).serialize()

    if parent:
        for module in modules:
            if module["machine_name"] == parent:
                if "submodules" not in module or not module["submodules"]:
                    module["submodules"] = []
                module["submodules"].append(serialized)
                break
    else:
        modules.append(serialized)

    if write:
        file_config.write()
