# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""
Helper function to compile latex file in a temp dir
"""

import logging as log
import re
import shutil
import subprocess
import sys
from pathlib import Path

from rich.live import Live
from rich.spinner import Spinner

# Match only lines beginning with INPUT
INPUT_RE = re.compile(r"^INPUT")
INPUT_STY = re.compile(r"^INPUT\s.*.(cls|def|sty)")
INPUT_FONTS = re.compile(r"^INPUT\s.*.(pfb|tfm)")
FONT_PUBLIC = re.compile(r"/public/.*/")


def run_latexmk(filename, mode, compdir):
    """Helper function to actually compile the latex file in a tmpdir"""
    # Generate fls file from tex file by running latexmk
    latexmk_cmd = [
        shutil.which("latexmk"),
        f"-{mode}",
        "-f",
        "-cd",
        f"-outdir={compdir}",
        "-interaction=nonstopmode",
        filename.name,
    ]
    try:
        with Live(
            Spinner("dots2", text="Compiling LaTeX project"),
            transient=True,
        ):
            subprocess.run(
                latexmk_cmd,
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
    except OSError as err:
        log.critical("%s", err.strerror)
        sys.exit(1)
    except subprocess.CalledProcessError as err:
        log.critical(
            "Error: %s failed with the following output:\n%s",
            err.cmd[0],
            err.stdout,
        )
        sys.exit(1)
    except TypeError as err:  # Typically when latexmk is missing and shutil
                              # gets a None as the first elem of cmdline list
        log.critical("%s", err)
        log.critical("Is latexmk installed and in PATH?")
        sys.exit(1)

    log.info(
        "LaTeX project successfully compiled with: %s", " ".join(latexmk_cmd)
    )
    fls_path = Path(compdir) / f"{filename.stem}.fls"
    log.debug("%s generated", fls_path.as_posix())
    return fls_path


def fls_input_files(fls_fileobj, lof_excl, skip_files, *, sty_files=False):
    """Helper function to return list on files marked as 'INPUT' in fls file"""
    deps = set()
    pkgs = {"System": set(), "Local": set()}
    for line in fls_fileobj:
        if INPUT_RE.match(line):
            p = Path(line.split()[-1])
            if (
                not p.is_absolute()
                and (p.as_posix() not in deps)
                and (p.as_posix() not in lof_excl)
                and (p.suffix not in skip_files)
            ):
                deps.add(p.as_posix())
                log.info("Add file: %s", p.as_posix())

        if sty_files:
            if INPUT_STY.match(line):
                p = Path(line.split()[-1])
                if p.is_absolute():
                    # Base is not a (La)TeX package; it is installed with even
                    # the most basic TeXlive/MikTeX installation
                    if (pdir := p.parent.name) != "base":
                        pkgs["System"].add(pdir)
                else:
                    pkgs["Local"].add(p.stem)
            elif INPUT_FONTS.match(line):
                p = Path(line.split()[-1])
                if p.is_absolute():
                    try:
                        fontdir = (
                            FONT_PUBLIC.search(str(p)).group(0).split("/")[2]
                        )
                    except AttributeError:
                        fontdir = p.parent.name
                    pkgs["System"].add(fontdir)

    return list(deps), pkgs
