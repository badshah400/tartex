# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

import sys
from pathlib import Path
import logging as log
from rich import print as richprint
from rich.prompt import Prompt

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
    wdir: Path, main_file: Path, user_path: Path, git_tag: str = ""
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
        out = out / (f"{main_file.stem}{git_tag}")
    elif (ext := out.suffix.lstrip(".")) in TAR_EXT:
        tar_ext = ext
    else:
        out = out.with_name(out.name)

    out = strip_tarext(out)
    log.debug("Processed output target basename: %s", out)
    return out, tar_ext


def tar_name_conflict(
    wdir: Path,  # calling dir
    filename: Path,  # main .tex/.fls filename
    tpath: str,  # full path to initial tarball name
    overwrite: bool = False,  # whether to overwrite tarball or not
    git_tag: str = "",  # full tag to be used for git-rev
):
    """
    Resolves conflict in case output tarball file already exists by either of
    the following options offered to user:

    * Overwriting existing file (automatically chosen if `overwrite` is `True`).
    * Asking for new tarball name (if tarball with new name already exists, exit with error).
    * Quit directly.

    :wdir: dir from which `tar_files()` is called (Path)
    :filename: main .tex/.fls file path (Path)
    :tpath: full filename of initial tarball (str)
    :overwrite: whether to overwrite existing tarball (optional; bool)
    :git_tag: full tag to be appended to tarball filename when `git-rev` is used (optional; str)

    :returns: new_tar_file and new extension if any (otherwise "") (tuple)
    """
    ext = Path(tpath).suffix.lstrip(".")

    if overwrite:
        log.warning(f"Overwriting existing tar file {tpath}")
        return tpath, ext
    richprint(
        "[bold red]A tar file with the same name"
        rf" \[{wdir / tpath}]"
        " already exists[/bold red]"
    )

    ocq = Prompt.ask(
        "What would you like to do "
        r"([bold blue]\[O][/bold blue]verwrite /"
        r" [bold green]\[C][/bold green]hoose new name /"
        r" *[bold red]\[Q][/bold red]uit)?"
    )
    if ocq.lower() in ["", "q"]:
        richprint(
            "[bold]Not overwriting existing tar file[/bold]\nQuitting",
            file=sys.stderr,
        )
        sys.exit(1)
    elif ocq.lower() == "c":
        new_name = Path(
            Prompt.ask("Enter [bold]new name[/bold] for tar file")
        ).expanduser()
        new_path, new_ext = proc_output_path(wdir, filename, new_name, git_tag)
        if new_ext:
            ext = new_ext
        new_path = Path(f"{new_path!s}.tar.{ext}").resolve()

        if new_path == tpath:
            richprint(
                "[bold red]Error: New name entered is also the same as"
                " existing tar file name[/bold red]\nQuitting",
                file=sys.stderr,
            )
            sys.exit(1)
        elif new_path.exists():
            richprint(
                "[bold red]Error: A tar file with the same name"
                rf" \[{(wdir / new_path)!s}] also"
                " exists[/bold red]\nQuitting",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            log.info("Tar file %s will be generated", new_path.as_posix())
            return new_path, ext
    elif ocq.lower() == "o":
        log.warning(f"Overwriting existing tar file {tpath}")
        return tpath, ext
    else:
        richprint(
            "[bold red]Error: Invalid response[/]\nQuitting.",
            file=sys.stderr,
        )
        sys.exit(1)
