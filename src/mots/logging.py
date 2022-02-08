# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Set up logging for mots."""
import logging
import logging.config
from pathlib import Path

logger = logging.getLogger(__name__)

LOG_FILE_PATH = Path("mots.log")
LOG_MAX_SIZE = 1024 * 1024 * 50
LOG_BACKUPS = 5


def init_logging(
    debug: bool = False,
    path: Path = LOG_FILE_PATH,
    log_max_size: int = LOG_MAX_SIZE,
    log_backups: int = LOG_BACKUPS,
):
    """Initialize default logger."""
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "standard": {
                    "format": "%(asctime)-13s %(module)-10s %(levelname)-8s %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": logging.DEBUG if debug else logging.WARNING,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "filename": path,
                    "maxBytes": log_max_size,
                    "backupCount": log_backups,
                    "encoding": "utf8",
                    "level": logging.DEBUG,
                },
            },
            "loggers": {
                "mots": {
                    "handlers": ["console", "file"],
                    "level": logging.DEBUG,
                },
            },
        }
    )
    logger.debug(f"Logging configured with log file @ {path}.")
