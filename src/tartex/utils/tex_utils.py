# vim:set et sw=4 ts=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

from enum import IntEnum
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

    return [
        Path(f) for f in [bib_name, bst_name] if (f and Path(f).is_file())
    ]


def latexmk_summary(err_msg: str) -> tuple[set[str], set[str]]:
    """Pick out potential lines of interest from a full latexmk error msg

    :err_msg: full latexmk error log as a string
    :returns: list of str representing a summary of important points collected
              from the full `err_msg`

    """
    LBR = r"(?:\n|\r\n)"
    RE_ERRORS: dict[str, Union[str, None]] = {
        # "search pattern"
        # : "replacement" or None
        r"^! LaTeX Error: (Environment .* undefined).$"
        : r"\1",
        r"^! LaTeX Error: (Missing \begin\{document\}).$"
        : r"\1",
        rf"^(.*){LBR}! (Emergency stop).{LBR}(.*)$"
        : r"\2: \1",
        r"^! LaTeX Error: (File `.*' not found.)$"
        : r"\1",
        r"^! (Package.* Error: .* not found):"
        : r"\1",
        rf"^! (Undefined control sequence).{LBR}(l\.\d+)\s*(.*)$"
        : r"\2 [\1]: \3",
        rf"^! (Too many \{{?\}}?'s.){LBR}(l\.\d+)(.*)$"
        : r"\2 [\1]: \3",
        r"^! (Missing \}?\{?\$? inserted)."
        rf"{LBR}(?:.*){LBR}(?:.*){LBR}(l\.\d+)\s(.*)$"
        : r"\2 [\1]: \3",
        r"^Runaway argument\?"
        : None,
        rf"^! (Misplaced alignment .*) \&\.{LBR}(l.\d+)\s*(.*\&)$"
        : r"\2 [\1]: \3",
    }

    err_lines = _get_filtered_lines(RE_ERRORS, err_msg)

    RE_WARNS: dict[str, Union[str, None]] = {
        r"^LaTeX Warning: (.*)\.$" : r"\1",
        rf"^Package (.*) Warning: (.*{LBR}?.*\.)$" : r"\1 warning: \2",
    }
    warn_lines: set[str] = _get_filtered_lines(
        RE_WARNS,
        err_msg,
        ignore=[
            "citation(s) may have changed",
            "standard defaults will be used",
            "There were undefined references",
            "Rerun to get cross-references right",
        ]
    )

    return (err_lines, warn_lines)


def _get_filtered_lines(
    filters: dict[str, Union[str, None]], msg: str, ignore: list[str] = []
) -> set[str]:
    """Return a set of filtred lines from `msg` using the `filtres` dict"""
    lines: set[str] = set()
    for key, val in filters.items():
        _mat = re.finditer(key, msg, re.MULTILINE)
        for _l in _mat:
            _g = _l.group()
            if val:
                for _ig in ignore:
                    if _ig.lower() in _g.lower():  # even if matching partly
                        break
                else:
                    lines.add(re.sub(key, val, _g).replace("\n", ""))

            else:
                lines.add(_g)

    return lines



class ExitCode(IntEnum):
    """Enums for TarTeX exit codes"""
    SUCCESS      = 0
    FAIL_GENERIC = 1
    FAIL_CACHE   = 2
    FAIL_GIT     = 3
    FAIL_LATEXMK = 4
    FAIL_TAR     = 5


class SetEncoder(json.JSONEncoder):
    """A class to allow JSONEncoder to interpret a set as a list"""

    def default(self, o: set) -> list:
        """
        Convert o (a set) into a sorted list

        :o: set
        :return: list
        """
        return sorted(o)
