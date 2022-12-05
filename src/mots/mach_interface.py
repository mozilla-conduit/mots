# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This module provides an API to integrate mots within mach.

Be careful to not break backward compatibility here, or you will
break mach!
"""

from __future__ import absolute_import

from argparse import Namespace

from mots.cli import create_parser, main
from mots.utils import check_for_updates


parser = create_parser
new_release_on_pypi = check_for_updates


def run(options):
    """Run mots given a dict of options."""
    main(
        args=Namespace(**options),
        skip_update_check=True,
    )
