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
from .tex_utils import SetEncoder, SUPP_REQ

HASH_METHOD = hashlib.sha256


def save_input_files_hash(
    cache_file: Path,
    files: set[Path],
    streams: set[str],
    packages: dict[str, set[str]],
) -> None:
    hash_dict: dict[str, str] = {}
    for p in files:
        try:
            with open(p, mode="rb") as f:
                hash_dict[str(p)] = hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            continue

    _cache = {
        "input_files": hash_dict,
        "streams": streams,
        "packages": packages,
    }
    with open(cache_file, mode="w") as f:
        json.dump(
            _cache,
            f,
            cls=SetEncoder,
            indent=4,
            ensure_ascii=True,
        )
    try:
        c_path_msg = f"~/{cache_file.relative_to(Path.home())}"
    except ValueError:
        c_path_msg = str(cache_file)
    log.info("Updated cache: %s", c_path_msg)
    return


def check_file_hash(cache_file: Path) -> bool:
    try:
        with open(cache_file, mode="r") as cf:
            cache_dict = json.load(cf)
    except Exception:
        return False

    # if any supplementary files are found as `streams` in the cache file, this
    # implies they are missing from the project dir and a recompile may be
    # required (otherwise file will be missing from tarball too). Log info.
    for supp in cache_dict["streams"]:
        if Path(supp).suffix.lstrip(".") in SUPP_REQ:
            log.info(
                "Missing supplementary file %s, try recompile ('-F')", supp
            )

    for filename in cache_dict["input_files"].keys():
        try:
            with open(filename, mode="rb") as _f:
                if (
                    cache_dict["input_files"][filename]
                    != hashlib.sha256(_f.read()).hexdigest()
                ):
                    return False
        except FileNotFoundError as err:
            log.warning("Unable to find file: %s", err.filename)
            return False
    else:
        return True
