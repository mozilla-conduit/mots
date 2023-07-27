# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Configuration classes used to initialize and manage mots in a repo."""

from __future__ import annotations

from collections import defaultdict
import io
import hashlib
import logging

from datetime import datetime
from pathlib import Path
from ruamel.yaml import YAML

from mots.bmo import get_bmo_data
from mots.directory import Directory, People
from mots.export import export_to_format
from mots.module import Module
from mots.utils import generate_machine_readable_name
from mots.settings import settings

logger = logging.getLogger(__name__)

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

QUICK_START_BLURB = "\n".join(
    (
        "See https://mots.readthedocs.io/en/latest/#quick-start for quick start",
        "documentation and how to modify this file.",
    )
)

MPL2 = "\n".join(
    (
        "This Source Code Form is subject to the terms of the Mozilla Public",
        "License, v. 2.0. If a copy of the MPL was not distributed with this",
        "file, You can obtain one at https://mozilla.org/MPL/2.0/.",
    )
)


class ValidationError(TypeError):
    """Thrown when a particular module is not valid."""

    pass


class FileConfig:
    """Loader and writer for filesystem based configuration."""

    def __init__(self, path: Path = settings.DEFAULT_CONFIG_FILEPATH):
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
                "hashes": {"config": None, "export": None},
                "export": {},
                "people": [],
                "modules": [],
            }
            self.write()
            logger.info(f"mots configuration initialized in {self.path}.")
        else:
            logger.warning(f"mots configuration file detected in {self.path}.")

    def load(self):
        """Load configuration from file."""
        with self.path.open("r", encoding="utf-8") as f:
            self.config = yaml.load(f)

    def check_hashes(self) -> list[str]:
        """Check that the hashes in the config are up to date.

        Upon calling this function, the existing configuration is copied and stripped
        of volatile keys, then a hash is calculated and compared against the old hash.

        If there is a mismatch, return non-zero exit code. Otherwise return 0.
        """
        errors = []
        config = self.config.copy()

        if "export" in self.config and "path" in self.config["export"]:
            with (self.repo_path / config["export"]["path"]).open("rb") as f:
                export = f.read()
        else:
            export = None

        original_hashes, hashes = calculate_hashes(self.config, export)

        for hash_key in ("config", "export"):
            if original_hashes.get(hash_key) != hashes.get(hash_key):
                errors.append(f"Mismatch in {hash_key} hash detected.")
                errors.append(
                    f"{hashes[hash_key]} does not match {original_hashes[hash_key]}"
                )
                errors.append(f"{hash_key} file is out of date.")

        return errors

    def write(self, hashes: dict | None = None):
        """Write configuration to file, and update the timestamp and hashes."""
        logger.debug(f"Writing configuration to {self.path}")
        self.config["updated_at"] = datetime.now().isoformat()
        self.config["hashes"] = hashes or {}
        with self.path.open("w", encoding="utf-8", newline="\n") as f:
            yaml.dump(self.config, f)


def reference_anchor_for_module(
    index: int,
    person: dict,
    key: str,
    file_config: FileConfig,
    directory: Directory,
    module: dict,
) -> None:
    """Associate person with a reference to a directory entry if possible.

    :param index: the position of the person in the referrer field
    :param person: a dictionary with information about the person to be added
    :param key: the key (e.g, "peers" or "owners_emeritus") that defines context
    :param file_config: config context being modified
    :param module: dictionary of the module in the config being modified


    This is needed so that ruamel.yaml can correctly reference anchors to people.
    """
    logger.debug(f"Setting reference to {person} as {key} in {module['machine_name']}")

    referrer = module["meta"][key] if key.endswith("_emeritus") else module[key]

    if person["bmo_id"] not in directory.people.by_bmo_id:
        # Person has to be added to directory before adding the reference.
        file_config.config["people"].append(person)
        directory.load_people()
        directory.people.refresh_by_bmo_id()
        referrer[index] = person
    else:
        # Associate the directory entry with the referrer.
        referrer[index] = file_config.config["people"][
            directory.people.by_bmo_id[person["bmo_id"]]
        ]


def calculate_hashes(config: dict, export: bytes) -> tuple[dict, dict]:
    """Calculate a hash of the yaml config file."""
    config = config.copy()

    # Exclude hashes and updated timestamp from hash generation
    original_hashes = config.pop("hashes", {})
    hashes = {}
    config.pop("updated_at", None)

    # Write actual config yaml dump to stream.
    with io.StringIO() as stream:
        yaml.dump(config, stream)
        content = stream.getvalue()

    config_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()
    hashes["config"] = config_hash

    if "export" in config:
        hashes["export"] = hashlib.sha1(export).hexdigest()

    return original_hashes, hashes


def clean(file_config: FileConfig, write: bool = True, refresh: bool = True):
    """Clean and re-sort configuration file.

    Load configuration from disk, sort modules and submodules by `machine_name`. If
    there is no valid `machine_name`, generate one. Reformat yaml content. Calculate
    and store hashes if needed. Write changes to disk if needed.

    :param file_config: an instance of :class:`FileConfig`
    :param write: if set to `True`, writes changes to disk.
    """
    people_keys = ("owners", "peers")
    emeritus_keys = [f"{k}_emeritus" for k in people_keys]
    file_config.load()
    directory = Directory(file_config)
    directory.load()

    people = list(file_config.config["people"])

    bmo_data = get_bmo_data(people)
    updated_people = People(people, bmo_data)

    people_to_sync = set(person["bmo_id"] for person in people if "nick" not in person)

    if refresh:
        # Use the updated list that was synchronized with Bugzilla.
        logger.info("Refreshing all people entries from Bugzilla.")
        file_config.config["people"] = updated_people.serialized
    else:
        # Use the original people list, and update entries only where needed.
        logger.warning("Only synchronizing new people with Bugzilla.")
        updated_people_dict = {
            updated_person["bmo_id"]: updated_person
            for updated_person in updated_people.serialized
        }
        for person in people:
            if person["bmo_id"] in people_to_sync:
                logger.info(f"Updated {person['bmo_id']} with new data.")
                person.update(updated_people_dict[person["bmo_id"]])
        file_config.config["people"] = people

    for i, module in enumerate(file_config.config["modules"]):
        if "machine_name" not in module:
            module["machine_name"] = generate_machine_readable_name(module["name"])

        for emeritus_key in emeritus_keys:
            if not (
                "meta" in module
                and module["meta"]
                and emeritus_key in module["meta"]
                and module["meta"][emeritus_key]
            ):
                continue
            for i, person in enumerate(module["meta"][emeritus_key]):
                if not isinstance(person, dict):
                    continue
                reference_anchor_for_module(
                    i, person, emeritus_key, file_config, directory, module
                )

        for key in people_keys:
            if key not in module or not module[key]:
                continue
            for i, person in enumerate(module[key]):
                reference_anchor_for_module(
                    i, person, key, file_config, directory, module
                )

        # Do the same for submodules.
        if "submodules" in module and module["submodules"]:
            module["submodules"].sort(key=lambda x: x["name"])
            for submodule in module["submodules"]:

                for emeritus_key in emeritus_keys:
                    if not (
                        "meta" in submodule
                        and submodule["meta"]
                        and emeritus_key in submodule["meta"]
                        and submodule["meta"][emeritus_key]
                    ):
                        continue
                    for i, person in enumerate(submodule["meta"][emeritus_key]):
                        if not isinstance(person, dict):
                            continue
                        reference_anchor_for_module(
                            i,
                            person,
                            emeritus_key,
                            file_config,
                            directory,
                            submodule,
                        )

                for key in people_keys:
                    if key not in submodule or not submodule[key]:
                        continue
                    for i, person in enumerate(submodule[key]):
                        reference_anchor_for_module(
                            i, person, key, file_config, directory, submodule
                        )
                if "machine_name" not in submodule:
                    submodule["machine_name"] = generate_machine_readable_name(
                        submodule["name"]
                    )

    file_config.config["modules"].sort(key=lambda x: x["machine_name"])
    file_config.config.yaml_set_start_comment(f"{MPL2}\n\n{QUICK_START_BLURB}")
    if write:
        # Write all changes.
        file_config.write()

        # Reload changes from disk so we can reset all anchors.
        file_config.load()

        nicks = []
        file_config.config["people"].sort(
            key=lambda person: person.get("nick", "").lower()
        )
        for person in file_config.config["people"]:
            machine_readable_nick = generate_machine_readable_name(
                person.get("nick", ""), keep_case=True
            )
            if machine_readable_nick in nicks or not machine_readable_nick:
                continue
            nicks.append(machine_readable_nick)
            person.yaml_set_anchor(machine_readable_nick)

        if "export" in file_config.config and "format" in file_config.config["export"]:
            export = export_to_format(
                directory, file_config.config["export"]["format"]
            ).encode("utf-8")
        else:
            export = None
        hashes = calculate_hashes(file_config.config, export)[1]
        file_config.write(hashes)


def validate(config: dict, repo_path: str) -> list[str] | None:
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
        error_msg = (
            f"Duplicate machine name(s) found: {', '.join(machine_names.keys())}"
        )
        return [error_msg]

    errors = []
    for module in config["modules"]:
        module = Module(repo_path=repo_path, **module)
        validation_errors = module.validate()
        if validation_errors:
            errors += validation_errors

    if errors:
        return errors
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
