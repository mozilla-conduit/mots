# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""This module sets up parsers and maps cli commands to methods."""

from datetime import datetime
from pathlib import Path
import argparse
import getpass
import logging
import sys

from mots import module
from mots import config
from mots.bmo import MissingBugzillaAPIKey, BMOClient
from mots.ci import validate_version_tag
from mots.directory import Directory
from mots.export import export_to_format
from mots.logging import init_logging
from mots.settings import settings
from mots.utils import (
    get_list_input,
    mkdir_if_not_exists,
    touch_if_not_exists,
    check_for_updates as _check_for_updates,
)
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
    errors = config.validate(file_config.config, file_config.repo_path) or []
    for error in errors:
        logger.error(error)
    sys.exit(1 if errors else 0)


def clean(args: argparse.Namespace) -> None:
    """Run clean methods for configuration file and write to disk."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    try:
        config.clean(file_config, refresh=args.refresh)
    except MissingBugzillaAPIKey:
        logger.error("Could not detect a Bugzilla API Key.")
        messages = (
            "Either set it in your environment (MOTS_BUGZILLA_API_KEY) or add it to ",
            "your settings file by running: ",
            "`mots settings write BUGZILLA_API_KEY`.",
            "You will be prompted to enter the API key after running this command.",
            "You can generate a Bugzilla API key in your User Preferences page under",
            "the API Keys tab.",
        )
        print("\n".join(messages))
        sys.exit(1)


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
            with out_path.open("w", encoding="utf-8", newline="\n") as f:
                logger.info(f"Writing output to specified file path ({out_path})...")
                f.write(output)
        else:
            # No output path could be determined, so output to standard out.
            print(output)
    else:
        # TODO: do more checks here to make sure we don't overwrite important things.
        logger.info(f"Writing output to specified file path ({args.out})...")
        with args.out.open("w", encoding="utf-8", newline="\n") as f:
            f.write(output)


def export_and_clean(args: argparse.Namespace) -> None:
    """Run clean, export, and clean again to save users keystrokes."""
    # The first clean checks mots.yaml for any issues and synchronizes with BMO.
    clean(args)

    # The export exports the yaml file to rst. This assumes that the export path is
    # defined in the configuration.
    export(args)

    # The last clean resets hashes
    clean(args)


def write(args: argparse.Namespace):
    """Set a specified settings variable to the provided value."""
    key = args.key[0]

    with settings.OVERRIDES_FILE.open("r", encoding="utf-8") as f:
        overrides = yaml.load(f) or {}

    if key not in settings.DEFAULTS:
        raise ValueError(f"{key} does not exist in defaults.")

    is_secure = key in settings.SECURE_KEYS

    if args.value is not None:
        value = args.value
    else:
        prompt = f"Enter value for {key}: "
        value = input(prompt) if not is_secure else getpass.getpass(prompt=prompt)

    _type = type(settings.DEFAULTS[key])

    if _type(value) == overrides.get(key):
        raise ValueError(f"{key} is already set to {value} in overrides file.")

    overrides[key] = _type(value)
    value_output = value if not is_secure else "*" * 10
    logger.info(
        f"{key} is now set to {value_output} ({_type.__name__}) in overrides file."
    )

    with settings.OVERRIDES_FILE.open("w", encoding="utf-8", newline="\n") as f:
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


def search(args: argparse.Namespace):
    """Search Bugzilla API for users, given an email address."""
    bmo_client = BMOClient()
    result = bmo_client.get_matches(args.match)
    logger.info(f"Found {len(result)} users.")
    logger.info("Tip: you can copy and paste a dictionary entry into a field.")

    for user in result:
        person = {"bmo_id": user["id"], "name": user["real_name"], "nick": user["nick"]}
        out = f"{person} -> {user['email']}"
        print(out)


def check_for_updates(args: argparse.Namespace) -> None:
    """CLI wrapper around _check_for_udpdates."""
    _check_for_updates(args.include_pre_releases)


def call_main_with_args():
    """Call `main` after creating a parser and parsing arguments.

    This method is used when running mots directly via the CLI. When mots is run via
    an integration (e.g., mach), then the integration must call `main` directly with
    the arguments.
    """
    parser = create_parser()
    args = parser.parse_args()
    main(args)


def main(
    args: argparse.Namespace,
    skip_update_check: bool = False,
) -> None:
    """Run startup commands and redirect to appropriate function."""
    mkdir_if_not_exists(settings.RESOURCE_DIRECTORY)
    touch_if_not_exists(settings.OVERRIDES_FILE)
    init_logging(debug=getattr(args, "debug", False))

    if hasattr(args, "func"):
        if skip_update_check:
            logger.debug("Skipping update check.")
        elif args.func != check_for_updates and settings.CHECK_FOR_UPDATES:
            try:
                _check_for_updates(settings.CHECK_PRE_RELEASES)
            except Exception as e:
                logger.warning("Could not check for updates.")
                logger.debug(e)
        logger.debug(f"Calling {args.func} with {args}...")
        st = datetime.now()
        try:
            args.func(args)
        except Exception as e:
            logger.exception(e)
        else:
            logger.info("Success!")
        et = datetime.now()
        logger.debug(f"{args.func} took {(et - st).total_seconds()} seconds.")
    else:
        # By default, print help to screen.
        create_parser().print_help()


def _add_path_argument(_parser):
    _parser.add_argument(
        "--path",
        "-p",
        type=Path,
        help="the path of the repo config file",
        default=settings.DEFAULT_CONFIG_FILEPATH,
    )


def create_parser(subcommand=None):
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

    user_parser = main_cli.add_parser("user", help="user operations")
    user_cli = user_parser.add_subparsers(title="user")

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
        (main_cli, export_and_clean, "perform automatic cleaning and exporting"),
        (main_cli, validate, "validate mots config"),
        (main_cli, check_for_updates, "check for new versions of mots"),
        (module_cli, add, "add a new module"),
        (module_cli, ls, "list all modules"),
        (module_cli, show, "show module details"),
        (settings_cli, write, "update settings variable and save to disk"),
        (settings_cli, read, "get settings variable, or all if no key is provided"),
        (user_cli, search, "search Bugzilla user database"),
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
    parsers["export-and-clean"].add_argument(*path_flags, **path_args)
    parsers["export-and-clean"].add_argument(
        "--format", "-f", type=str, choices=("rst",), help="the format of exported data"
    )
    parsers["export-and-clean"].add_argument(
        "--out", "-o", type=Path, help="the file path to output to"
    )

    parsers["write"].add_argument("key", nargs=1, help="the settings key to set")
    parsers["write"].add_argument(
        "value", nargs="?", help="the value to set key to if present"
    )

    parsers["read"].add_argument(
        "key",
        nargs="?",
        help="fetch the value of key if provided, or all keys otherwise",
    )

    parsers["search"].add_argument("match", nargs=1, help="a search string")
    parsers["check-for-updates"].add_argument(
        "--include-pre-releases",
        action="store_true",
        help="include pre releases in check",
        default=settings.CHECK_PRE_RELEASES,
    )

    parsers["init"].add_argument(*path_flags, **path_args)
    parsers["validate"].add_argument(*path_flags, **path_args)
    parsers["clean"].add_argument(*path_flags, **path_args)
    parsers["check-hashes"].add_argument(*path_flags, **path_args)

    for _parser in (parsers["clean"], parsers["export-and-clean"]):
        # Add common --refresh argument to both parsers.
        _parser.add_argument(
            "--refresh", action="store_true", help="refresh user data from Bugzilla"
        )

    subcommand_parsers = {
        "user": user_parser,
        "module": module_parser,
        "settings": settings_parser,
    }

    if not subcommand:
        return parser
    if subcommand in subcommand_parsers:
        return subcommand_parsers[subcommand]
    if subcommand not in parsers:
        raise ValueError(f"{subcommand} not found.")
    return parsers[subcommand]
