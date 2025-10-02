# vim:set et sw=4 ts=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""
Helper function to compile latex file in a temp dir
"""

from io import TextIOWrapper
import logging as log
import re
import shutil
import subprocess
from pathlib import Path

from rich.live import Live
from rich.spinner import Spinner

# Match only lines beginning with INPUT
INPUT_RE = re.compile(r"^INPUT")
INPUT_STY = re.compile(r"^INPUT\s.*.(cls|def|sty)")
INPUT_FONTS = re.compile(r"^INPUT\s.*.(pfb|tfm)")
FONT_PUBLIC = re.compile(r"/public/.*/")


class LatexmkError(Exception):
    """
    class representing possible errors when using latexmk to compile
    project
    """

    def __init__(
        self, returncode: int, cmd: str, summ: str = "", desc: str = ""
    ):
        """Initialise LatexmkError class

        :returncode: a return code associated with the error
        :cmd: command used to run compilation
        :stdout: output to stdout
        :stderr: output to stderr

        """
        self._retcode = returncode
        self._command = cmd
        self._summary = summ
        self._desc = desc

    @property
    def code(self) -> int:
        """code from the command"""
        return self._retcode

    @property
    def cmd(self) -> str:
        """full command used for compilation"""
        return self._command

    @property
    def summary(self) -> str:
        """short summary of error from command"""
        return self._summary

    @property
    def description(self) -> str:
        """detailed error log from command"""
        return self._desc

    @property
    def msg(self) -> tuple[str, str]:
        """get a tuple of error summary, description"""
        return (self._summary, self._desc)


def run_latexmk(
    filename: Path,
    mode: str,
    compdir: str,
    timeout: int = 300,
    silent: bool = False,
) -> Path:
    """Helper function to actually compile the latex file in a tmpdir"""

    latexmk_bin = shutil.which("latexmk")
    if not latexmk_bin:
        raise LatexmkError(1, "latexmk", "unable to find `latexmk` in PATH")

    # Generate fls file from tex file by running latexmk
    latexmk_cmd = [
        latexmk_bin,
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
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        raise LatexmkError(
            1,
            " ".join(latexmk_cmd),
            f"process timed out after {timeout} seconds",
        )
    except OSError as err:
        raise LatexmkError(1, " ".join(latexmk_cmd), err.strerror or "")
    except subprocess.CalledProcessError as err:
        raise LatexmkError(
            1,
            " ".join(latexmk_cmd),
            f"{err.cmd[0]} failed to compile project",
            err.stdout,  # detailed latexmk log is in stdout
        )

    if not silent:
        log.info(
            "LaTeX project successfully compiled with: %s",
            " ".join(latexmk_cmd),
        )
    fls_path = Path(compdir) / f"{filename.stem}.fls"
    log.debug("%s generated", fls_path.as_posix())
    return fls_path


def fls_input_files(
    fls_fileobj: TextIOWrapper,
    skip_files: list[str],
    *,
    sty_files: bool = False,
) -> tuple[set[Path], dict[str, set[str]]]:
    """Helper function to return list on files marked as 'INPUT' in fls file"""

    deps: set = set()
    pkgs: dict[str, set[str]] = {"System": set(), "Local": set()}
    for line in fls_fileobj:
        if INPUT_RE.match(line):
            p = Path(line.split()[-1])
            if not p.is_absolute() and (p.suffix not in skip_files):
                deps.add(p)

        if sty_files:
            if INPUT_STY.match(line):
                p = Path(line.split()[-1])
                if p.is_absolute():
                    # Base is not a (La)TeX package; it is installed with even
                    # the most basic TeXlive/MikTeX installation
                    if (pdir := p.parent.name) != "base":
                        pkgs["System"].add(pdir)
                else:
                    pkgs["Local"].add(p.name)
            elif INPUT_FONTS.match(line):
                p = Path(line.split()[-1])
                if p.is_absolute():
                    _mat = FONT_PUBLIC.search(str(p))
                    fontdir = (
                        _mat.group(0).split("/")[2] if _mat else p.parent.name
                    )
                    pkgs["System"].add(fontdir)

    return deps, pkgs
