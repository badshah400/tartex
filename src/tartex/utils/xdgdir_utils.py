# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"Helper module for XDG based cache dir discovery"

from .hash_utils import HASH_METHOD
import os
from pathlib import Path
from tartex.__about__ import __appname__

XDG_CACHE_HOME = Path(os.getenv("XDG_CACHE_HOME") or Path.home() / ".cache")

def app_cache_dir(main_file: Path) -> Path:
    """
    Set up and return path to unique cache dir to be used for `main_file`.
    Every `main_file` must have its own unique cache dir inside the global
    cache path `${XDG_CACHE_HOME}/tartex/`.

    :main_file: main .tex|.fls file [Path]
    :returns: Path to cache dir [Path]

    """
    cache_dir = XDG_CACHE_HOME / __appname__
    prj_dir = main_file.resolve().parent

    # Use bottom two parent dirs and join them using "_"
    path_parts = prj_dir.parts
    if len(path_parts) >= 2:
        dir_short_name = '_'.join(
            str(prj_dir).split(os.sep)[-2:]
        )
    else:
        dir_short_name = prj_dir.name
    # Append a short dir hash making the dir name unique
    dir_short_hash = HASH_METHOD(
        str(main_file.resolve()).encode("utf-8")
    ).hexdigest()[:8]
    prj_cache_dir = cache_dir / (
        f"{dir_short_name}_{dir_short_hash}"
    )
    prj_cache_dir.mkdir(parents=True, exist_ok=True)
    return prj_cache_dir
