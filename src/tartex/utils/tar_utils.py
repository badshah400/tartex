# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

from pathlib import Path
# Allowed tar extensions
TAR_EXT = ["bz2", "gz", "xz"]

# Default compression
TAR_DEFAULT_COMP = "gz"


def strip_tarext(filename: Path):
    """Strip '.tar(.EXT)' from filename"""
    while filename.suffix.lstrip(".") in TAR_EXT + ["tar"]:
        filename = filename.with_suffix("")
    return filename



