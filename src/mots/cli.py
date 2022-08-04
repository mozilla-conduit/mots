# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""This module sets up parsers and maps cli commands to methods."""

import argparse
from datetime import datetime
import logging
from pathlib import Path
import sys

from mots import module
from mots import config
from mots.ci import validate_version_tag
from mots.directory import Directory
from mots.export import export_to_format
from mots.logging import init_logging
from mots.settings import settings
from mots.utils import get_list_input, mkdir_if_not_exists, touch_if_not_exists
from mots.yaml import yaml
from mots import __version__


logger = logging.getLogger(__name__)


def init(args: argparse.Namespace) -> None:
    """Initialize mots configuration file."""
    file_config = config.FileConfig(Path(args.path))
    file_config.init()


def ls(args: argparse.Namespace) -> None:
    """List modules."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    module.ls(file_config.config["modules"])


def show(args: argparse.Namespace) -> None:
    """Show given module details."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    module.show(file_config.config["modules"], args.module)


def validate(args: argparse.Namespace) -> None:
    """Validate configuration and show error output if applicable."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    errors = config.validate(file_config.config, file_config.repo_path)
    for error in errors:
        logger.error(error)
    sys.exit(1 if errors else 0)


def clean(args: argparse.Namespace) -> None:
    """Run clean methods for configuration file and write to disk."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    config.clean(file_config)


def check_hashes(args: argparse.Namespace) -> None:
    """Check stored hashes against calculated hashes and exit with appropriate code."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    errors = file_config.check_hashes()
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)


def query(args: argparse.Namespace) -> None:
    """Query list of files for module information."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    directory = Directory(file_config)
    directory.load()
    result = directory.query(*args.paths)
    for path, modules in result.path_map.items():
        module_names = ",".join([m.machine_name for m in modules])
        print(f"{path}:{module_names}\n")


def add(args: argparse.Namespace) -> None:
    """Add a new module or submodule to repo configuration file."""
    params = {
        "machine_name": input(
            "Enter a machine name (alphanumeric characters and underscores)"
            " for the new module (e.g. core_accessibility): "
        ),
        "name": input("Enter a human readable name (e.g. Core: Accessibility): "),
        "description": input("Enter a description for the new module: "),
        "owners": get_list_input("Enter a comma separated list of owner bugzilla IDs"),
        "peers": get_list_input("Enter a comma separated list of peer bugzilla IDs"),
        "includes": get_list_input("Enter a comma separated list of paths to include"),
        "excludes": get_list_input("Enter a comma separated list of paths to exclude"),
    }

    params["owners"] = [{"bmo_id": int(bmo_id)} for bmo_id in params["owners"]]
    params["peers"] = [{"bmo_id": int(bmo_id)} for bmo_id in params["peers"]]

    parent = input("Enter a machine name of the parent module (optional): ") or None
    file_config = config.FileConfig(Path(args.path))
    config.add(params, file_config, parent=parent, write=True)


def ci(args: argparse.Namespace) -> None:
    """Perform CI checks or validations."""
    try:
        validate_version_tag()
    except ValueError as e:
        logger.error(e)
        sys.exit(1)


def version():
    """Return version information."""
    return __version__


def export(args: argparse.Namespace) -> None:
    """Export repo configuration and write to disk, or print to stdout as needed."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    directory = Directory(file_config)
    directory.load()

    frmt = (
        args.format
        if args.format
        else file_config.config.get("export", {}).get(
            "format", settings.DEFAULT_EXPORT_FORMAT
        )
    )

    # Render output based on provided format.
    output = export_to_format(directory, frmt)

    if not args.out:
        # Explicit output path was not provided, try to get it from config.
        if file_config.config.get("export", {}).get("path"):
            out_path = Path(file_config.config["export"]["path"])
            with out_path.open("w") as f:
                logger.info(f"Writing output to specified file path ({out_path})...")
                f.write(output)
        else:
            # No output path could be determined, so output to standard out.
            print(output)
    else:
        # TODO: do more checks here to make sure we don't overwrite important things.
        logger.info(f"Writing output to specified file path ({args.out})...")
        with args.out.open("w") as f:
            f.write(output)


def write(args: argparse.Namespace):
    """Set a specified settings variable to the provided value."""
    key = args.key[0]
    value = args.value[0]
    with settings.OVERRIDES_FILE.open("r") as f:
        overrides = yaml.load(f) or {}

    if key not in settings.DEFAULTS:
        raise ValueError(f"{key} does not exist in defaults.")

    _type = type(settings.DEFAULTS[key])

    if _type(value) == overrides.get(key):
        raise ValueError(f"{key} is already set to {value} in overrides file.")

    overrides[key] = _type(value)
    print(f"{key} is now set to {value} ({_type.__name__}) in overrides file.")

    with settings.OVERRIDES_FILE.open("w") as f:
        yaml.dump(overrides, f)


def read(args: argparse.Namespace):
    """Print the value of a specified settings variable.

    If no key is provided, prints all available settings variables.
    """

    def out_template(key: str, value: str):
        return f"{key}: {value} ({type(value).__name__})"

    if not args.key:
        for key, value in settings.settings.items():
            print(out_template(key, value))
        return

    key = args.key

    if key not in settings.settings:
        raise ValueError(f"{key} does not exist in defaults.")
    value = settings.settings[key]
    print(out_template(key, value))


def main():
    """Run startup commands and redirect to appropriate function."""
    parser = create_parser()
    args = parser.parse_args()

    mkdir_if_not_exists(settings.RESOURCE_DIRECTORY)
    touch_if_not_exists(settings.OVERRIDES_FILE)
    init_logging(debug=args.debug)

    if hasattr(args, "func"):
        logger.debug(f"Calling {args.func} with {args}...")
        st = datetime.now()
        args.func(args)
        et = datetime.now()
        logger.debug(f"{args.func} took {(et - st).total_seconds()} seconds.")
    else:
        parser.print_help()


def _add_path_argument(_parser):
    _parser.add_argument(
        "--path",
        "-p",
        type=Path,
        help="the path of the repo config file",
        default=settings.DEFAULT_CONFIG_FILEPATH,
    )


def create_parser():
    """Create parser, subparsers, and arguments."""
    parsers = {}
    parser = argparse.ArgumentParser(description="main command line interface for mots")
    parser.add_argument("--debug", action="store_true", help="enable debug output")
    parser.add_argument("--version", action="version", version=version())
    main_cli = parser.add_subparsers(title="commands")
    module_parser = main_cli.add_parser("module", help="module operations")
    _add_path_argument(module_parser)
    module_cli = module_parser.add_subparsers(title="module")

    settings_parser = main_cli.add_parser("settings", help="settings operations")
    settings_cli = settings_parser.add_subparsers(title="settings")

    # Create path argument template.
    path_flags = ("--path", "-p")
    path_args = {
        "type": Path,
        "help": "the path of the repo config file",
        "default": settings.DEFAULT_CONFIG_FILEPATH,
    }

    for _cli, func, help_text in (
        (main_cli, ci, "perform CI checks or operations"),
        (main_cli, init, "initialize mots configuration in repo"),
        (main_cli, clean, "clean mots config"),
        (main_cli, check_hashes, "check mots config and export hashes"),
        (main_cli, query, "query the module directory"),
        (main_cli, export, "export the module directory"),
        (module_cli, add, "add a new module"),
        (module_cli, ls, "list all modules"),
        (module_cli, show, "show module details"),
        (module_cli, validate, "validate mots config"),
        (settings_cli, write, "update settings variable and save to disk"),
        (settings_cli, read, "get settings variable, or all if no key is provided"),
    ):
        name = func.__name__.replace("_", "-")
        parsers[name] = _cli.add_parser(name, help=help_text)
        parsers[name].set_defaults(func=func)

    # Add custom arguments where needed.
    parsers["query"].add_argument("paths", nargs="+", help="a list of paths to query")
    parsers["query"].add_argument(*path_flags, **path_args)

    parsers["export"].add_argument(
        "--format", "-f", type=str, choices=("rst",), help="the format of exported data"
    )
    parsers["export"].add_argument(
        "--out", "-o", type=Path, help="the file path to output to"
    )
    parsers["export"].add_argument(*path_flags, **path_args)

    parsers["write"].add_argument("key", nargs=1, help="the settings key to set")
    parsers["write"].add_argument("value", nargs=1, help="the value to set key to")

    parsers["read"].add_argument(
        "key",
        nargs="?",
        help="fetch the value of key if provided, or all keys otherwise",
    )

    parsers["init"].add_argument(*path_flags, **path_args)
    parsers["validate"].add_argument(*path_flags, **path_args)
    parsers["clean"].add_argument(*path_flags, **path_args)
    parsers["check-hashes"].add_argument(*path_flags, **path_args)

    return parser
