# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

from pathlib import Path
from typing import Union
import json

import re


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


def add_files(patterns: list[str], dir: Path) -> set[Path]:
    """
    Return list of additional user specified/globbed file paths,
    if they exist
    """
    files: set[Path] = set()
    for fpatt in patterns:
        files.update(set(dir.glob(f"**/{fpatt}")))

    return files


# TODO: account for possible multiple bib file usage
def bib_file(tex_fname: Path) -> list[Union[Path, None]]:
    """Return relative path to bib file"""
    bibre = re.compile(r"^\\bibliography\{.*\}")
    bib_name = None
    bstre = re.compile(r"^\\bibliographystyle\{.*\}")
    bst_name = None
    with open(tex_fname, encoding="utf-8") as f:
        for line in f:
            m_bib = bibre.search(line)
            m_bst = bstre.search(line)
            if m_bib:
                bib_name = m_bib.group()
                continue
            if m_bst:
                bst_name = m_bst.group()
                continue
            if bib_name and bst_name:
                break

    if bib_name:
        bib_name = re.sub(r"^\\bibliography\{", "", bib_name).rstrip("}")
        bib_name += ".bib" if bib_name.split(".")[-1] != ".bib" else ""
    if bst_name:
        bst_name = re.sub(r"^\\bibliographystyle\{", "", bst_name).rstrip("}")
        bst_name += ".bst" if bst_name.split(".")[-1] != ".bst" else ""

    return [Path(f) for f in [bib_name, bst_name] if Path(f).is_file()]

class SetEncoder(json.JSONEncoder):
    """A class to allow JSONEncoder to interpret a set as a list"""

    def default(self, o: set) -> list:
        """
        Convert o (a set) into a sorted list

        :o: set
        :return: list
        """
        return sorted(o)
