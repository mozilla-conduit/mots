# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""CI/CD related methods."""

import logging
import os

from mots import __version__
from mots.settings import settings

logger = logging.getLogger(__name__)


def validate_version_tag():
    """Check the current version against the CircleCI tag."""
    KEY = settings.CIRCLECI_TAG_KEY
    circle_tag = os.getenv(KEY)
    if not circle_tag:
        raise ValueError(f"{KEY} environment variable missing or blank.")

    if circle_tag != __version__:
        raise ValueError(
            f"{KEY} does not match version ({circle_tag} vs. {__version__})"
        )

    logger.info(f"{KEY} matches version.")
