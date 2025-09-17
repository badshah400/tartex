# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""utilities for saving and checking file hash"""

import hashlib
import json
import logging as log
from pathlib import Path
from .tex_utils import SetEncoder

HASH_METHOD = hashlib.sha256

def save_input_files_hash(
    cache_file: Path,
    files: set[Path],
    packages: dict[str, set[Path]],
) -> None:
    hash_dict: dict[str, str] = {}
    wdir = cache_file.parent
    for p in files:
        try:
            with open(p, mode="rb") as f:
                try:
                    rel_path = p.relative_to(wdir)
                except ValueError:
                    rel_path = p.absolute()
                hash_dict[str(rel_path)] = hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            continue

    _cache = {"input_files": hash_dict, "packages": packages}
    with open(cache_file, mode="w") as f:
        json.dump(
            _cache,
            f,
            cls=SetEncoder,
            indent=4,
            ensure_ascii=True,
        )

def check_file_hash(cache_file: Path) -> bool:
    try:
        with open(cache_file, mode="r") as cf:
            cache_dict = json.load(cf)
    except Exception:
        return False

    for filename in cache_dict["input_files"].keys():
        try:
            with open(filename, mode="rb") as _f:
                if cache_dict["input_files"][filename] != hashlib.sha256(_f.read()).hexdigest():
                    return False
        except FileNotFoundError as err:
            log.warn(err)
            return False
    else:
        return True
