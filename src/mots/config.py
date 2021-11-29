# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Configuration classes used to initialize and manage mots in a repo."""
import logging

from datetime import datetime
from pathlib import Path
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_style = '""'

DEFAULT_CONFIG_FILEPATH = "./mots.yaml"


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
            now = datetime.now()
            self.config = {
                "repo": str(Path(self.path).resolve().parts[-2]),
                "created_at": now,
                "updated_at": None,
                "modules": None,
            }
            self.write()
            logger.info(f"mots configuration initialized in {self.path}.")
        else:
            logger.warning(f"mots configuration file detected in {self.path}.")

    def load(self):
        """Load configuration from file."""
        with open(self.path, "r") as f:
            self.config = yaml.load(f)

    def write(self):
        """Write configuration to file, and update the timestamp."""
        self.config["updated_at"] = datetime.now()
        with open(self.path, "w") as f:
            yaml.dump(self.config, f)
