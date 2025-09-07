# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

from pathlib import Path
import logging as log

# Allowed tar extensions
TAR_EXT = ["bz2", "gz", "xz"]

# Default compression
TAR_DEFAULT_COMP = "gz"


def strip_tarext(filename: Path):
    """Strip '.tar(.EXT)' from filename"""
    while filename.suffix.lstrip(".") in TAR_EXT + ["tar"]:
        filename = filename.with_suffix("")
    return filename


def proc_output_path(
    wdir: Path,
    main_file: Path,
    user_path: Path,
    git_tag: str = ""
):
    """
    Returns the output tar file path (sans any '.tar.?z' suffix) after
    resolving the value passed to '--output' as part of cmdline options.

    Also sets the tar ext if determined from '--output' argument.

    Uses `user_path` instead of the value of `--output` argument if passed.
    """

    # If self.args.output is absolute, '/' simply returns it as a PosixPath
    out = (wdir / user_path.expanduser()).resolve()
    tar_ext = ""

    if out.is_dir():  # If dir, set to DIR/${main_file}.tar.gz
        log.debug("%s is an existing dir", out)
        out = out / (
            f"{main_file.stem}{f'-{git_tag}' if git_tag else ''}"
        )
    elif (ext := out.suffix.lstrip(".")) in TAR_EXT:
        tar_ext = ext
    else:
        out = out.with_name(out.name)

    out = strip_tarext(out)
    log.debug("Processed output target basename: %s", out)
    return out, tar_ext


