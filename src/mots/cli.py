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
import sys
from pathlib import Path

from mots import module
from mots.config import FileConfig
from mots.directory import Directory
from mots.logging import init_logging
from mots.config import DEFAULT_CONFIG_FILEPATH

from mots.utils import get_list_input

logger = logging.getLogger(__name__)


class CLI:
    """Wrap methods and call with the correct arguments."""

    @staticmethod
    def init(args):
        """Call `file_config.init` with correct arguments."""
        file_config = FileConfig(Path(args.path))
        file_config.init()

    @staticmethod
    def ls(args):
        """Call `module.ls` with correct arguments."""
        file_config = FileConfig(Path(args.path))
        file_config.load()
        return module.ls(file_config.config["modules"])

    @staticmethod
    def show(args):
        """Call `module.show` with correct arguments."""
        file_config = FileConfig(Path(args.path))
        file_config.load()
        return module.show(file_config.config["modules"], args.module)

    @staticmethod
    def validate(args):
        """Call `module.validate` with correct arguments."""
        file_config = FileConfig(Path(args.path))
        file_config.load()
        return module.validate(file_config.config, args.repo_path)

    @staticmethod
    def clean(args):
        """Call `module.clean` with correct arguments."""
        file_config = FileConfig(Path(args.path))
        file_config.load()
        return module.clean(file_config)

    @staticmethod
    def query(args):
        """Call `directory.query` with correct arguments."""
        file_config = FileConfig(Path(args.path))
        file_config.load()
        directory = Directory(file_config)
        directory.load()
        result, rejected = directory.query(*args.paths)
        for path in result:
            modules = result[path]
            module_names = ",".join([m.machine_name for m in modules])
            owners = ",".join([",".join(m.owners) for m in modules])
            sys.stdout.write(f"{path}:{module_names}:{owners}\n")

    @staticmethod
    def add(args):
        """Prompt user to add a new module."""
        params = {
            "machine_name": input("Enter machine name of new module: "),
            "name": input("Enter a human readable name: "),
            "owners": get_list_input("Enter a comma separated list of owners"),
            "peers": get_list_input("Enter a comma separated list of peers"),
            "includes": get_list_input(
                "Enter a comma separated list of paths to include"
            ),
            "excludes": get_list_input(
                "Enter a comma separated list of paths to exclude"
            ),
        }
        parent = input("Enter a machine name of the parent module (optional): ") or None
        file_config = FileConfig(Path(args.path))
        module.add(params, file_config, parent=parent, write=True)


def main():
    """Redirect to appropriate function."""
    parser = create_parser()
    args = parser.parse_args()

    init_logging(debug=args.debug)

    if hasattr(args, "func"):
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
    init_parser.set_defaults(func=CLI.init)

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
    list_parser.set_defaults(func=CLI.ls)

    add_parser = module_parsers.add_parser("add", help="add a new module")
    add_parser.set_defaults(func=CLI.add)

    show_parser = module_parsers.add_parser("show", help="show a module")
    show_parser.add_argument("module", help="name of the module to show")
    show_parser.set_defaults(func=CLI.show)

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
    validate_parser.set_defaults(func=CLI.validate)

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
    clean_parser.set_defaults(func=CLI.clean)

    query_parser = subparsers.add_parser("query", help="query the module directory")
    query_parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="the path of the repo config file",
        default=DEFAULT_CONFIG_FILEPATH,
    )
    query_parser.add_argument("paths", nargs="+", help="a list of paths to query")
    query_parser.set_defaults(func=CLI.query)

    return parser
