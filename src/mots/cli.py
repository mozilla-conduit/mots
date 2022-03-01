# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
usage: mots [-h] [--debug] {init,module,validate,clean,query} ...

main command line interface for mots

optional arguments:
  -h, --help            show this help message and exit
  --debug               enable debug output

commands:
  {init,module,validate,clean,query}
    init                initialize mots configuration in repo
    module              module_operations
    validate            validate mots config for current repo
    clean               clean mots config for current repo
    query               query the module directory
"""
import argparse
from datetime import datetime
import logging
from pathlib import Path

from mots import module
from mots import config
from mots.directory import Directory
from mots.export import export_to_format
from mots.logging import init_logging
from mots.config import DEFAULT_CONFIG_FILEPATH

from mots.utils import get_list_input

logger = logging.getLogger(__name__)


def init(args: argparse.Namespace) -> None:
    """Call `file_config.init` with correct arguments."""
    file_config = config.FileConfig(Path(args.path))
    file_config.init()


def ls(args: argparse.Namespace) -> None:
    """Call `module.ls` with correct arguments."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    module.ls(file_config.config["modules"])


def show(args: argparse.Namespace) -> None:
    """Call `module.show` with correct arguments."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    module.show(file_config.config["modules"], args.module)


def validate(args: argparse.Namespace) -> None:
    """Call `config.validate` with correct arguments."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    config.validate(file_config.config, args.repo_path)


def clean(args: argparse.Namespace) -> None:
    """Call `config.clean` with correct arguments."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    config.clean(file_config)


def query(args: argparse.Namespace) -> None:
    """Call `directory.query` with correct arguments."""
    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    directory = Directory(file_config)
    directory.load()
    result = directory.query(*args.paths)
    for path, modules in result.path_map.items():
        module_names = ",".join([m.machine_name for m in modules])
        print(f"{path}:{module_names}\n")


def add(args: argparse.Namespace) -> None:
    """Prompt user to add a new module."""
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


def export(args: argparse.Namespace) -> None:
    """Call `export.export_to_format` with relevant parameters."""
    DEFAULT_EXPORT_FORMAT = "rst"

    file_config = config.FileConfig(Path(args.path))
    file_config.load()
    directory = Directory(file_config)
    directory.load()

    frmt = (
        args.format
        if args.format
        else file_config.config.get("export", {}).get("format", DEFAULT_EXPORT_FORMAT)
    )

    # Render output based on provided format.
    output = export_to_format(directory, frmt)

    if not args.out:
        # Explicit output path was not provided, try to get it from config.
        if file_config.config.get("export", {}).get("path"):
            out_path = file_config.config["export"]["path"]
            with open(out_path, "w") as f:
                logger.info(f"Writing output to specified file path ({out_path})...")
                f.write(output)
        else:
            # No output path could be determined, so output to standard out.
            print(output)
    else:
        # TODO: do more checks here to make sure we don't overwrite important things.
        logger.info(f"Writing output to specified file path ({args.out})...")
        with open(args.out, "w") as f:
            f.write(output)


def main():
    """Redirect to appropriate function."""
    parser, subparsers = create_parser()
    args = parser.parse_args()

    init_logging(debug=args.debug)

    if hasattr(args, "func"):
        logger.debug(f"Calling {args.func} with {args}...")
        st = datetime.now()
        args.func(args)
        et = datetime.now()
        logger.debug(f"{args.func} took {(et - st).total_seconds()} seconds.")
    else:
        parser.print_help()


def create_parser():
    """Create parser, subparsers, and arguments."""
    parser = argparse.ArgumentParser(description="main command line interface for mots")
    parser.add_argument("--debug", action="store_true", help="enable debug output")
    subparsers = parser.add_subparsers(title="commands")

    init_parser = subparsers.add_parser(
        "init", help="initialize mots configuration in repo"
    )
    init_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo to initialize",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    init_parser.set_defaults(func=init)

    module_parser = subparsers.add_parser("module", help="module_operations")
    module_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo config file",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    module_parsers = module_parser.add_subparsers(title="module")

    list_parser = module_parsers.add_parser("list", help="list all modules")
    list_parser.set_defaults(func=ls)

    add_parser = module_parsers.add_parser("add", help="add a new module")
    add_parser.set_defaults(func=add)

    show_parser = module_parsers.add_parser("show", help="show a module")
    show_parser.add_argument("module", help="name of the module to show")
    show_parser.set_defaults(func=show)

    validate_parser = subparsers.add_parser(
        "validate", help="validate mots config for current repo"
    )
    validate_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo config file",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    validate_parser.add_argument(
        "--repo-path",
        "-r",
        type=str,
        help="the path of the repo",
        default=".",
    )
    validate_parser.set_defaults(func=validate)

    clean_parser = subparsers.add_parser(
        "clean", help="clean mots config for current repo"
    )
    clean_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo config file",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    clean_parser.add_argument(
        "--repo-path",
        "-r",
        type=str,
        help="the path of the repo",
        default=".",
    )
    clean_parser.set_defaults(func=clean)

    query_parser = subparsers.add_parser("query", help="query the module directory")
    query_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo config file",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    query_parser.add_argument("paths", nargs="+", help="a list of paths to query")
    query_parser.set_defaults(func=query)

    export_parser = subparsers.add_parser("export", help="export the module directory")
    export_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo config file",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    export_parser.add_argument(
        "--format", "-f", type=str, help="the format of exported data"
    )
    export_parser.add_argument(
        "--out", "-o", type=str, help="the file path to output to"
    )
    export_parser.set_defaults(func=export)

    return parser, subparsers
