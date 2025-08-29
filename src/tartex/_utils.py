# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

from pathlib import Path
from typing import Union

from rich import print as richprint

# Auxilliary file extensions to ignore
# taken from latexmk manual:
# https://www.cantab.net/users/johncollins/latexmk/latexmk-480.txt
AUXFILES = [
    ".aux",
    ".bcf",
    ".fls",
    ".idx",
    ".lof",
    ".lot",
    ".out",
    ".toc",
    ".blg",
    ".ilg",
    ".log",
    ".xdv",
    ".fdb_latexmk",
]

# Supplementary files that are usually required as part of tarball
SUPP_REQ = ["bbl", "ind"]

# Allowed tar extensions
TAR_EXT = ["bz2", "gz", "xz"]

# Default compression
TAR_DEFAULT_COMP = "gz"


def strip_tarext(filename: Path):
    """Strip '.tar(.EXT)' from filename"""
    while filename.suffix.lstrip(".") in TAR_EXT + ["tar"]:
        filename = filename.with_suffix("")
    return filename


def summary_msg(
    nfiles, tarname: Union[Path, None] = None, wdir: Union[Path, None] = None
):
    """Return summary msg to print at end of run"""

    def _num_tag(n: int):
        return f"[bold]{n} file" + ("s" if n > 1 else "") + "[/]"

    if tarname:
        try:
            tarname_rel = tarname.relative_to(wdir if wdir else tarname.root)
        except ValueError:
            tarname_rel = tarname
        finally:
            richprint(
                f"[cyan]Summary: :package: [bold]{tarname_rel}[/] generated with"
                f" {_num_tag(nfiles)}.[/]"
            )
    else:
        richprint(
            f"[cyan]Summary: :clipboard: {_num_tag(nfiles)} to include.[/]"
        )


def add_files(patterns: list[str], dir: Path) -> set[Path]:
    """
    Return list of additional user specified/globbed file paths,
    if they exist
    """
    files: set[Path] = set()
    for fpatt in patterns:
        files.update(set(dir.glob(fpatt)))

    return files
