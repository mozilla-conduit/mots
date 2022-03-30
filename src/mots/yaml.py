# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Configuration classes used to initialize and manage mots in a repo."""

import logging

from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


def load_yaml():
    """Load and return a ruamel.yaml.YAML instance."""
    yaml = YAML()
    yaml.indent(
        mapping=2,
        sequence=4,
        offset=2,
    )
    return yaml


yaml = load_yaml()
