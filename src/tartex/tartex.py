# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""tartex module"""

import fnmatch
import json
import logging as log
import math
import os
import re
import sys
import tarfile as tar
from contextlib import nullcontext
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union

from rich import print as richprint
from rich.prompt import Prompt

from tartex import _latex
from tartex._parse_args import parse_args
from tartex._git_rev import GitRev, git_checkout
from tartex._utils import *


def _set_main_file(name: str) -> Union[Path, None]:
    main_file = Path(name).resolve()
    if main_file.suffix not in [".fls", ".tex"]:
        # ...otherwise try adding the .fls/.tex suffix to main_file
        for f in [str(main_file) + suff for suff in [".fls", ".tex"]]:
            if Path(f).is_file():
                main_file = Path(f)
                break
        else:
            raise FileNotFoundError(f"File {main_file.name}[.tex|.fls] not found.")
    return main_file if main_file.is_file() else None

class TarTeX:
    """
    Class to help build  a tarball including all source files needed to
    re-compile your LaTeX project."
    """

    # pylint: disable=too-many-instance-attributes

    pkglist_name = "TeXPackages.json"

    def __init__(self, args):
        self.args = parse_args(args)
        log.basicConfig(
            format="[%(levelname)s] %(message)s",
            level=(
                (log.INFO // self.args.verbose)
                if self.args.verbose > 0
                else log.WARN
            ),
        )
        self.cwd = Path.cwd()
        try:
            self.main_file = _set_main_file(self.args.fname)
            if not self.main_file:
                log.critical("Error: File not found - %s", self.args.fname)
                sys.exit(1)

        except FileNotFoundError as err:
            log.critical(f"Error: {err}")
            sys.exit(1)

        if self.args.git_rev:
            try:
                self.GR = GitRev(
                    self.main_file.parent, self.args.git_rev or "HEAD"
                )
                self.tar_file_git_tag = f"{self.GR.id()}.tar"
                self.mtime = self.GR.mtime()
            except Exception:
                sys.exit(1)
        else:
            self.tar_file_git_tag = ""


        self.pdf_stream = None
        # Set default tar extension...
        self.tar_ext = TAR_DEFAULT_COMP
        # ..but use specified output's TAR_EXT extension if any...
        if self.args.output:
            self.args.output = self._proc_output_path()

        # ...but overwrite TAR_EXT if tar compression option passed
        if self.args.bzip2:
            self.tar_ext = "bz2"
        if self.args.gzip:
            self.tar_ext = "gz"
        if self.args.xz:
            self.tar_ext = "xz"

        tar_base = (
            Path(f"{self.args.output}.tar")
            if self.args.output
            else Path(
                f"{self.main_file.stem}{f'-{self.tar_file_git_tag}' if self.args.git_rev else ''}"
            ).with_suffix(".tar")
        )
        tar_file = self.cwd / tar_base  # returns tar_base when absolute
        self.tar_file_w_ext = tar_file.with_suffix(f".tar.{self.tar_ext}")
        log.debug("Output tarball '%s' will be generated", self.tar_file_w_ext)

        self.req_supfiles = {}
        self.add_files = self.args.add.split(",") if self.args.add else []
        excludes = self.args.excl.split(",") if self.args.excl else []
        excl_lists = (self.main_file.parent.glob(f"{L}") for L in excludes)

        self.excl_files = [
            f.relative_to(self.main_file.parent).as_posix()
            for L in excl_lists
            for f in L
        ]

        # If .bbl/.ind is missing in source dir, then it is not in
        # self.excl_files (result of globbing files in srcdir) even if the user
        # passes a matching wildcard to exclude it with "-x".
        # Extend self.excl_files specifically in these cases
        for glb in excludes:
            self.excl_files.extend(
                [
                    f
                    for f in [
                        self.main_file.with_suffix(f".{g}") for g in SUPP_REQ
                    ]
                    if fnmatch.fnmatch(f.name, glb)
                ]
            )

        if self.excl_files:
            log.debug(" ".join(excl_lists))
            log.info(
                "List of excluded files: %s",
                ", ".join([Path(x).as_posix() for x in self.excl_files]),
            )

        self.force_tex = False if self.args.git_rev else self.args.latexmk_tex
        if not self.force_tex:
            # If force_tex is not set by user options,
            # set to ps if source dir contains ps/eps files
            # or to pdf otherwise
            src_ps = [
                str(p)
                for ext in ["eps", "ps"]
                for p in self.main_file.parent.glob(f"**/*.{ext}")
            ]
            self.force_tex = "ps" if src_ps else "pdf"
            log.info(
                "Latexmk will use %slatex for processing, if needed",
                self.force_tex,
            )

        self.pkglist = None

    # TODO: Re-structure function to make it readable, currently it is a bit of
    # a hodge-podge of `if...else` branches.
    def input_files(self):
        """
        Returns non-system input files needed to compile the main tex file.

        Input files are directly taken from `git ls-tree -r` if `self.git_rev`
        is true. In this case, user specified additional files and exclusions
        are ignored.

        Otherwise, uses `.fls` file, including trying to compile the
        main tex file using `latexmk` if it cannot find the fls file in the
        source dir.
        """

        if self.args.git_rev:
            log.debug(
                "Using `git ls-tree` to determine files to include in tarball"
            )
            deps = self.GR.ls_tree_files()
            # Process the --excl files
            for f in self.excl_files:  # Remove the file if it exists in the set
                deps.discard(f)
        if (
            not self.main_file.with_suffix(".fls").exists()
            or self.args.force_recompile
        ) and not self.args.git_rev:
            with TemporaryDirectory() as compile_dir:
                log.info(
                    "LaTeX recompile forced"
                    if self.args.force_recompile
                    else f"{self.main_file.stem}.fls file not found in"
                    f" {self.main_file.parent.as_posix()}"
                )
                log.info("LaTeX compile directory: %s", compile_dir)
                try:
                    fls_path = _latex.run_latexmk(
                        self.main_file.with_suffix(".tex"),
                        self.force_tex,
                        compile_dir,
                    )
                except Exception:
                    # Clean-up after latexmk failure
                    os.remove(self.tar_file_w_ext)
                    log.debug(
                        "Cleaning up empty tarball after latexmk failure: %s",
                        self.tar_file_w_ext.relative_to(Path.cwd()),
                    )
                    sys.exit(1)

                if self.args.with_pdf:
                    with open(fls_path.with_suffix(".pdf"), "rb") as f:
                        self.pdf_stream = f.read()

                with open(fls_path, encoding="utf-8") as f:
                    deps, pkgs = _latex.fls_input_files(
                        f,
                        self.excl_files,
                        AUXFILES,
                        sty_files=self.args.packages,
                    )

                self.mtime = os.path.getmtime(fls_path)
                main_pdf = Path(compile_dir) / self.main_file.with_suffix(".pdf")
                if self.args.with_pdf:
                    log.info("Add contents as BytesIO: %s", main_pdf)
                for ext in SUPP_REQ:
                    if app := self._missing_supp(
                        self.main_file.with_suffix(f".{ext}"), compile_dir, deps
                    ):
                        self.req_supfiles[
                            self.main_file.with_suffix(f".{ext}")
                        ] = app
        else:
            # If .fls exists, this assumes that all INPUT files recorded in it
            # are also included in source dir
            if (fls_f := self.main_file.with_suffix(".fls")).exists():
                self.mtime = os.path.getmtime(fls_f)
                with open(self.main_file.with_suffix(".fls"), encoding="utf8") as f:
                    deps_from_fls, pkgs = _latex.fls_input_files(
                        f, self.excl_files, AUXFILES, sty_files=self.args.packages
                    )
                    if not self.args.git_rev:
                        deps = deps_from_fls

                    if self.args.packages:
                        self.pkglist = json.dumps(pkgs, cls=SetEncoder).encode(
                            "utf8"
                        )

            else:  # perhaps using git ls-tree; fls file is (as expected) untracked or cleaned
                self.mtime = os.path.getmtime(self.main_file)
                if self.args.packages:
                    log.warn("Cannot generate list of packages due to missing %s file",
                             self.main_file.with_suffix(".fls"))
                    self.args.packages = False

            if self.args.with_pdf:
                main_pdf = self.main_file.with_suffix(".pdf")
                try:
                    with open(main_pdf, "rb") as f:
                        self.pdf_stream = f.read()
                        log.info("Add file: %s", main_pdf.relative_to(self.cwd))
                except FileNotFoundError:
                    log.warning(
                        f"Unable to find '{main_pdf}' in {self.cwd}, skipping..."
                    )
                    self.args.with_pdf = False

        if self.args.bib:
            for f in bib_file(self.main_file.with_suffix(".tex")):
                try:
                    deps.add(f.as_posix())
                    log.info("Add file: %s", deps[-1])
                    if re.match(r".bst", f.suffix):
                        pkgs["Local"].add(deps[-1])
                except Exception:
                    pass

        if self.add_files:
            for f in add_files(self.add_files, self.main_file.parent):
                f_relpath_str = f.relative_to(self.main_file.parent).as_posix()
                if f_relpath_str in deps:
                    log.warning(
                        "Manually included file %s already added", f_relpath_str
                    )
                    continue
                deps.add(f_relpath_str)
                log.info("Add user specified file: %s", f_relpath_str)

        if self.args.packages:
            log.info(
                "System TeX/LaTeX packages used: %s",
                ", ".join(sorted(pkgs["System"])),
            )

            self.pkglist = json.dumps(pkgs, cls=SetEncoder).encode("utf8")
        return deps

    def tar_files(self):
        """
        Generates a tarball consisting of non-system input files needed to
        recompile your latex project.
        """
        full_tar_name = Path(f"{self.tar_file_w_ext}")

        wdir = self.main_file.resolve().parent
        os.chdir(wdir)
        log.debug("Switching working dir to %s", wdir.as_posix())
        if self.args.list:
            file_list = self.input_files()
            if self.pdf_stream:
                file_list += [self.main_file.with_suffix(".pdf").name]
            self._print_list(file_list)
        else:
            try:
                f = tar.open(full_tar_name, mode=f"x:{self.tar_ext}")
                with f:
                    self._do_tar(f)
                    if self.args.summary:
                        summary_msg(
                            len(f.getmembers()),
                            self.cwd / full_tar_name,
                            self.cwd,
                        )
            except PermissionError as err:
                log.critical(
                    "Cannot write to %s, %s",
                    full_tar_name.parent,
                    err.strerror.lower(),
                )
                sys.exit(1)
            except FileExistsError:
                try:
                    full_tar_name = self._tar_name_conflict(full_tar_name)
                    # At this stage, there is either a new name for the tar
                    # file or user wants to overwrite existing file. In either
                    # case, calling tar.open() with 'w' mode should be OK.
                    f = tar.open(full_tar_name, mode=f"w:{self.tar_ext}")
                    with f:
                        self._do_tar(f)
                        if self.args.summary:
                            summary_msg(
                                len(f.getmembers()),
                                self.cwd / full_tar_name,
                                self.cwd,
                            )
                except PermissionError as err:
                    log.critical(
                        "Cannot write to %s, %s",
                        full_tar_name.parent,
                        err.strerror.lower(),
                    )
                    sys.exit(1)
        os.chdir(self.cwd)
        log.debug("Reset working dir to %s", os.getcwd())

    def _tar_name_conflict(self, tpath):
        if self.args.overwrite:
            log.warning(f"Overwriting existing tar file {tpath}")
            return tpath
        richprint(
            "[bold red]A tar file with the same name"
            rf" \[{self.cwd / tpath}]"
            " already exists[/bold red]"
        )

        owr = Prompt.ask(
            "What would you like to do "
            r"([bold blue]\[O][/bold blue]verwrite /"
            r" [bold green]\[C][/bold green]hoose new name /"
            r" *[bold red]\[Q][/bold red]uit)?"
        )
        if owr.lower() in ["", "q"]:
            richprint(
                "[bold]Not overwriting existing tar file[/bold]\nQuitting",
                file=sys.stderr,
            )
            sys.exit(1)
        elif owr.lower() == "c":
            new_name = Path(
                Prompt.ask("Enter [bold]new name[/bold] for tar file")
            ).expanduser()
            new_path = Path(
                f"{self._proc_output_path(new_name)!s}.tar.{self.tar_ext}"
            ).resolve()

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
                    rf" \[{(self.cwd / new_path)!s}] also"
                    " exists[/bold red]\nQuitting",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                log.info("Tar file %s will be generated", new_path.as_posix())
                return new_path
        elif owr.lower() == "o":
            log.warning(f"Overwriting existing tar file {tpath}")
            return tpath
        else:
            richprint(
                "[bold red]Error: Invalid response[/]\nQuitting.",
                file=sys.stderr,
            )
            sys.exit(1)

    def _do_tar(self, tar_obj):
        def _tar_add_file(
            file_name,
        ):  # helper func to add file <file_name> to <tar_obj>
            tinfo = tar_obj.gettarinfo(file_name)
            tinfo.uid = tinfo.gid = 0
            tinfo.uname = tinfo.gname = ""
            tar_obj.addfile(tinfo, open(file_name, "rb"))
            log.info("Add file: %s", file_name)

        cntxt = (
            git_checkout(self.GR.git_bin, self.GR.repo, self.GR.rev)
            if self.args.git_rev
            else
            nullcontext()
        )
        with cntxt:
            for dep in self.input_files():
                try:
                    _tar_add_file(dep)
                except FileNotFoundError:
                    log.warning(
                        "Skipping INPUT file '%s', not found amongst sources; try"
                        " forcing a LaTeX recompile ('-F').",
                        dep,
                    )
                    continue

        def _tar_add_bytesio(obj, file_name):
            # helper func to add `obj` as BytesIO with filename <file_name> to <tar_obj>
            tinfo = tar_obj.tarinfo(file_name)
            tinfo.size = len(obj)
            tinfo.mtime = self.mtime
            tinfo.uid = tinfo.gid = 0
            tinfo.uname = tinfo.gname = ""
            tar_obj.addfile(tinfo, BytesIO(obj))

        if self.pkglist:
            log.info(
                "Adding list of packages as BytesIO object: %s",
                self.pkglist_name,
            )
            _tar_add_bytesio(self.pkglist, self.pkglist_name)

        for fpath, byt in self.req_supfiles.items():
            log.info("Adding %s as BytesIO object", fpath.name)
            _tar_add_bytesio(byt, fpath.name)
        if self.pdf_stream:
            _tar_add_bytesio(self.pdf_stream, self.main_file.with_suffix(".pdf").name)

    def _proc_output_path(self, user_path: Union[Path, None] = None):
        """
        Returns the output tar file path (sans any '.tar.?z' suffix) after
        resolving the value passed to '--output' as part of cmdline options.

        Also sets the tar ext if determined from '--output' argument.

        Uses `user_path` instead of the value of `--output` argument if passed.
        """

        # If self.args.output is absolute, '/' simply returns it as a PosixPath
        if user_path:
            out = (self.cwd / user_path.expanduser()).resolve()
        else:
            out = (self.cwd / self.args.output.expanduser()).resolve()

        if out.is_dir():  # If dir, set to DIR/main.tar.gz
            log.debug("%s is an existing dir", out)
            out = (
                out
                / (
                    f"{self.main_file.stem}-{self.tar_file_git_tag}"
                    if self.args.git_rev
                    else self.main_file.stem
                )
            ).with_suffix(f".tar.{self.tar_ext}")
        elif (ext := out.suffix.lstrip(".")) in TAR_EXT:
            self.tar_ext = ext
        else:
            out = out.with_name(
                f"{out.name}.tar.{TAR_DEFAULT_COMP}"  # no tar ext stripping needed here
            )

        out = strip_tarext(out)
        log.debug("Processed output target basename: %s", out)
        return out

    def _print_list(self, ls):
        """helper function to print list of files in a pretty format"""
        idx_width = int(math.log10(len(ls))) + 1
        for i, f in enumerate(sorted([str(i) for i in ls])):
            richprint(f"{i + 1:{idx_width}}.", end=" ")
            print(f)
        for r in sorted(self.req_supfiles):
            richprint(f"{'*':>{idx_width + 1}}", end=" ")
            print(f"{r.name}")
        if self.args.packages:
            richprint(f"{'*':>{idx_width + 1}}", end=" ")
            print(f"{self.pkglist_name}")
        if self.args.summary:
            summary_msg(
                len(ls) + len(self.req_supfiles) + (1 if self.pkglist else 0)
            )

    def _missing_supp(self, fpath, tmpdir, deps):
        """Handle missing supplementary file from orig dir, if req"""
        if (
            fpath not in deps  # bbl file not in source dir
            and (Path(tmpdir) / fpath.name).exists()  # Implies it's req
            and fpath not in self.excl_files  # Not explicitly excluded
        ):
            log.debug("Required file '%s' not in source dir", fpath.name)
            log.info(
                "Add contents as BytesIO: %s",
                Path(tmpdir) / fpath.name,
            )
            return (Path(tmpdir) / fpath.name).read_bytes()

        return None


def make_tar():
    """Build tarball with command line arguments processed by argparse"""
    t = TarTeX(sys.argv[1:])
    t.tar_files()


class SetEncoder(json.JSONEncoder):
    """A class to allow JSONEncoder to interpret a set as a list"""

    def default(self, o):
        """
        Convert o (a set) into a sorted list

        :o: set
        :return: list
        """
        return sorted(o)


if __name__ == "__main__":
    make_tar()
