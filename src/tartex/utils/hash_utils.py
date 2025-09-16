# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""utilities for saving and checking file hash"""

import hashlib
import json
from pathlib import Path

HASH_METHOD = hashlib.sha256

def save_input_files_hash(files: set[Path], cache_file: Path) -> None:
    hash_dict: dict[str, str] = {}
    wdir = cache_file.parent
    for p in files:
        try:
            with open(p, mode="rb") as f:
                try:
                    rel_path = p.relative_to(wdir)
                except ValueError:
                    rel_path = p.absolute()
                hash_dict[str(rel_path)] = hashlib.file_digest(f, HASH_METHOD).hexdigest()
        except FileNotFoundError:
            continue

    with open(cache_file, mode="w") as f:
        json.dump(hash_dict, f, indent=4, ensure_ascii=True)

def check_file_hash(cache_file: Path) -> bool:
    try:
        with open(cache_file, mode="r") as cf:
            hash_dict = json.load(cf)
    except Exception:
        return False

    for filename in hash_dict.keys():
        with open(filename, mode="rb") as _f:
            if hash_dict[filename] != hashlib.file_digest(_f, HASH_METHOD).hexdigest():
                return False
                break
    else:
        return True
