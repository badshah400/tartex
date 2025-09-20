# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""tartex module"""

import errno
import fnmatch
import json
import logging as log
import os
import re
import sys
from contextlib import nullcontext
from pathlib import Path
from rich import (
    print as richprint,
    logging as richlog,
    highlighter,
)
from tempfile import TemporaryDirectory
from typing import Union

from tartex import _latex
from tartex._parse_args import parse_args
from tartex._git_rev import GitRev, git_checkout
import tartex.utils.msg_utils as _tartex_msg_utils
import tartex.utils.tex_utils as _tartex_tex_utils
import tartex.utils.tar_utils as _tartex_tar_utils
import tartex.utils.hash_utils as _tartex_hash_utils
import tartex.utils.xdgdir_utils as _tartex_xdg_utils
from tartex._tar import Tarballer

try:
    from contextlib import chdir
# contextlib.chdir is only available from Python 3.10 onwards
except ImportError:
    from contextlib import contextmanager

    @contextmanager  # type: ignore [no-redef]
    def chdir(p: Path):
        cwd = Path.cwd()
        try:
            os.chdir(p)
            yield p
        except Exception as err:
            raise err
        finally:
            os.chdir(cwd)

##################################
## HELPER CLASSES AND FUNCTIONS ##
##################################


class CheckFailError(Exception):
    """Exception raised when `--check` fails"""

    def __init__(self, msg=""):
        """init CheckFail exception"""
        super().__init__(msg)
        self._msg = msg

    def __str__(self):
        return f"Check failed: {self._msg}"


def _check_err_missing(
    _ref: Tarballer,
    _tgt: Tarballer,
    *,
    supp_files: set[Path] = set(),
    indicator: str = "*",
) -> bool:
    """
    Compares objects included in _ref and _tgt and return True if the former
    contains files missing from the latter. Logs accordingly.

    If non-empty, warns instead of declaring errors on missing `supp_files`.
    """
    non_exist_files = set([f for f in _ref.objects() if not f.exists()])
    non_exist_files.difference_update(supp_files)
    excluded = _ref.objects().difference(_tgt.objects())
    excluded.difference_update(non_exist_files.union(supp_files))

    if non_exist_files or excluded:
        if non_exist_files:
            log.info(
                "Files needed for compilation not found (deleted?): %s",
                ", ".join([f.as_posix() for f in non_exist_files]),
            )
            richprint(
                "[bold bright_red]Files needed for compilation missing (deleted?):[/]"
            )
            for f in non_exist_files:
                richprint(indicator, end=" ")
                print(f"{f!s}")

        if excluded:
            log.debug(
                "Files needed for compilation excluded from tarball: %s",
                ", ".join([f.as_posix() for f in excluded]),
            )
            richprint(
                "[bold bright_red]Files needed for compilation not included:[/]"
            )
            for f in excluded:
                richprint(indicator, end=" ")
                print(f"{f!s}")

        print()  # blank line to section off errors
        return True
    else:
        return False


def _check_warn_extra(
    _ref: Tarballer,
    _tgt: Tarballer,
    _indicator: str = "*",
) -> bool:
    """
    Compares objects included in _ref and _tgt and return True if the
    latter contains files missing from the former. Logs accordingly.
    """
    if _extra := _tgt.objects().difference(_ref.objects()):
        log.debug(
            "Files not essential to compilation added to tarball: %s",
            ", ".join([f.as_posix() for f in _extra]),
        )
        richprint("[yellow]Files not essential to compilation added:[/]")
        for f in _extra:
            richprint(_indicator, end=" ")
            print(f"{f!s}")
        else:
            print()

        return True
    else:
        return False


def _set_main_file(name: str) -> Union[Path, None]:
    """
    Return fully resolved file name after adding an appropriate suffix, if
    necessary. Raises `FileNotFoundError` if neither the input str, nor a
    version of it with '.tex' or '.fls' extension, point to any existing file.
    """
    main_file = Path(name).resolve()
    if main_file.suffix not in [".fls", ".tex"]:
        # ...otherwise try adding the .fls/.tex suffix to main_file
        for f in [str(main_file) + suff for suff in [".fls", ".tex"]]:
            if Path(f).is_file():
                main_file = Path(f)
                break
        else:
            raise FileNotFoundError(
                errno.ENOENT,
                "Main input file not found",
                main_file.with_suffix(".(tex|fls)").name
            )
    if main_file.is_file():
        return main_file
    else:
        raise FileNotFoundError(
            errno.ENOENT, "Main input file not found", main_file.name,
        )


################
## MAIN CLASS ##
################


class TarTeX:
    """
    Class to help build  a tarball including all source files needed to
    re-compile your LaTeX project."
    """

    pkglist_name = "TeXPackages.json"

    def __init__(self, args):
        self.args = parse_args(args)
        log_level = (
            (log.INFO // self.args.verbose)
            if self.args.verbose > 0
            else log.WARN
        )
        log.basicConfig(
            format="%(message)s",
            level=log_level,
            handlers=[
                richlog.RichHandler(
                    show_time=False,
                    show_path=False,
                    highlighter=highlighter.NullHighlighter(),
                )
            ],
        )
        self.cwd = Path.cwd()
        try:
            self.main_file = _set_main_file(self.args.fname)
        except FileNotFoundError as err:
            log.critical(f"{err.strerror}: {err.filename}")
            sys.exit(1)

        self.filehash_cache = (
            _tartex_xdg_utils.app_cache_dir(self.main_file)
            / f"{self.main_file.stem}.cache"
        )

        if self.args.git_rev:
            try:
                self.GR = GitRev(
                    self.main_file.parent, self.args.git_rev or "HEAD"
                )
                self.tar_file_git_tag = f"-{self.GR.id()}.tar"
            except Exception:
                sys.exit(1)
        else:
            self.tar_file_git_tag = ""

        self.pdf_stream = None
        # ..but use use specified output's TAR_EXT extension if any...
        self.tar_ext = ""
        if self.args.output:
            self.args.output, self.tar_ext = _tartex_tar_utils.proc_output_path(
                self.cwd,
                self.main_file,
                self.args.output,
                self.tar_file_git_tag,
            )

        self.tar_file_w_ext = self._tar_filename()
        self.tar_ext = self.tar_file_w_ext.suffix.lstrip(".")
        log.debug("Output tarball name: '%s'", self.tar_file_w_ext)

        self.req_supfiles = {}
        self.add_files = self.args.add.split(",") if self.args.add else []
        excludes = self.args.excl.split(",") if self.args.excl else []
        excl_lists = (self.main_file.parent.glob(f"**/{L}") for L in excludes)

        self.excl_files = set(
            [
                f.relative_to(self.main_file.parent)
                for L in excl_lists
                for f in L
            ]
        )
        # Do not exclude main tex file even if matched by `--excl` glob
        self.excl_files.discard(
            self.main_file.with_suffix(".tex").relative_to(
                self.main_file.parent
            )
        )

        # If .bbl/.ind is missing in source dir, then it is not in
        # self.excl_files (result of globbing files in srcdir) even if the user
        # passes a matching wildcard to exclude it with "-x".
        # Extend self.excl_files specifically in these cases
        for glb in excludes:
            self.excl_files.update(
                [
                    f
                    for f in [
                        self.main_file.with_suffix(f".{g}")
                        for g in _tartex_tex_utils.SUPP_REQ
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

    def input_files(self, tarf: Tarballer, silent: bool = False) -> None:
        """
        Returns non-system input files needed to compile the main tex file.

        Input files are directly taken from `git ls-tree -r` if `self.git_rev`
        is true. In this case, user specified additional files and exclusions
        are ignored.

        Otherwise, uses `.fls` file, including trying to compile the
        main tex file using `latexmk` if it cannot find the fls file in the
        source dir.
        """

        pkgs: dict[str, set[str]] = {}
        if self.args.git_rev:
            log.debug(
                "Using `git ls-tree` to determine files to include in tarball"
            )
            deps, pkgs = self.input_files_from_git(tarf, silent=silent)

        # If .fls is the user supplied "main file", this assumes that all INPUT
        # files recorded in it are also included in source dir and skips any
        # missing ones (unless force recompiling)
        elif self.main_file.suffix == ".fls" and not self.args.force_recompile:
            deps, pkgs = self.input_files_from_srcfls(tarf, silent=silent)

        # When "main file" is ".tex" and recompile has been forced by user
        # option `--force-recompile`
        elif self.args.force_recompile:
            deps, pkgs = self.input_files_from_recompile(tarf, silent=silent)

        # Most typical case: main file is ".tex", no force recompile, try cache
        # first, recompile if input files are missing or their hash don't match
        else:
            deps, pkgs = self.input_files_from_cache(tarf, silent=silent)

        if self.args.bib:
            tarf.app_files(*self._add_bib(pkgs))

        if self.add_files:
            tarf.app_files(*self._add_user_files())

        if self.excl_files:  # Remove files in excl list
            tarf.drop_files(*self.excl_files)

        if self.args.packages:
            log.info(
                "System TeX/LaTeX packages used: %s",
                ", ".join(sorted(pkgs["System"])),
            )

            self.pkglist = json.dumps(
                pkgs, cls=_tartex_tex_utils.SetEncoder
            ).encode("utf8")
            tarf.app_stream(
                self.pkglist_name,
                self.pkglist,
                comm=f"Adding list of used LaTeX packages: {self.pkglist_name}",
            )

    def input_files_from_git(
        self, tarf: Tarballer, silent: bool = False
    ) -> tuple[set[Path], dict[str, set[str]]]:
        """
        Get input files from `git ls-tree <REVISION>`
        :returns: TODO

        """
        if not silent:
            log.info("Getting files from git-tree")

        _deps = self.GR.ls_tree_files()
        _pkgs: dict[str, set[str]] = {}
        # Process the --excl files
        tarf.app_files(*_deps)
        tarf.set_mtime(self.GR.mtime())
        if self.args.packages:
            try:
                with open(
                    self.main_file.with_suffix(".fls"), encoding="utf-8"
                ) as f:
                    _, _pkgs = _latex.fls_input_files(
                        f,
                        _tartex_tex_utils.AUXFILES,
                        sty_files=self.args.packages,
                    )
            except FileNotFoundError:
                if not silent:
                    log.warning(
                        "Missing .fls file in source dir; %s will not be saved",
                        self.pkglist_name,
                    )
                self.args.packages = False
            except Exception as err:
                raise err
        return _deps, _pkgs

    def input_files_from_recompile(
        self,
        tarf: Tarballer,
        minimal: bool = False,
        cache_update: bool = False,
        silent: bool = False,
    ) -> tuple[set[Path], dict[str, set[str]]]:
        """
        Determines set of input files and list of LaTeX packages used by
        running explicit re-compilation of project in an out-of-tree temporary
        directory.

        If minimal is `True`, omits adding any files other than those
        absolutely needed for compilation, such as user specified bib files,
        etc., or, likewise, excluding files matching user specified exclusion
        patterns if any.

        Returns tuple: (Set of Path objects representing input files, dict of
        LaTeX packages used for compilation)
        """
        _deps: set[Path] = set()
        _pkgs: dict[str, set[str]] = {}
        with TemporaryDirectory() as compile_dir:
            if not silent:
                log.info(
                    f"LaTeX recompile {'forced' if self.args.force_recompile else 'required'}"
                )
                log.info("LaTeX compile directory: %s", compile_dir)
            try:
                fls_path = _latex.run_latexmk(
                    self.main_file.with_suffix(".tex"),
                    self.force_tex,
                    compile_dir,
                    silent=silent,
                )
            except Exception as e:
                raise e

            tarf.set_mtime(os.path.getmtime(fls_path))
            with open(fls_path, encoding="utf-8") as f:
                _deps, _pkgs = _latex.fls_input_files(
                    f,
                    _tartex_tex_utils.AUXFILES,
                    sty_files=self.args.packages,
                )
                tarf.app_files(*_deps)

                # Supplementary files, pkg lists are all transient — they only
                # live in the temporary `compile_dir`; so we need to save them
                # as streams inside this file-open context.
                self._add_supplement_streams(Path(compile_dir), _deps, tarf)
                if not minimal:
                    if self.args.with_pdf:
                        self._add_pdf_stream(fls_path.with_suffix(".pdf"), tarf)

                if cache_update:
                    _tartex_hash_utils.save_input_files_hash(
                        Path(self.filehash_cache),
                        _deps,
                        tarf.streams(),
                        _pkgs
                    )
                return _deps, _pkgs

    def input_files_from_srcfls(
        self, _t: Tarballer, silent: bool = False
    ) -> tuple[set[Path], dict[str, set[str]]]:
        """Get input files from '.fls' in source dir"""

        if not silent:
            log.info(
                "Reading input files from project fls file: '%s'",
                self.main_file.name
            )

        _deps: set[Path] = set()
        _pkgs: dict[str, set[str]] = {}

        fls_f = self.main_file.with_suffix(".fls")
        try:
            with open(fls_f, encoding="utf8") as f:
                _deps, _pkgs = _latex.fls_input_files(
                    f,
                    _tartex_tex_utils.AUXFILES,
                    sty_files=self.args.packages,
                )
                _t.set_mtime(os.path.getmtime(fls_f))

        except FileNotFoundError:
            if self.args.packages:
                if not silent:
                    log.warning(
                        "Cannot generate list of packages due to missing %s file",
                        fls_f,
                    )
                self.args.packages = False

        except Exception as err:
            raise err

        _t.app_files(*_deps)

        if self.args.with_pdf:
            self._add_pdf_stream(self.main_file.with_suffix(".pdf"), _t)
        return _deps, _pkgs

    def input_files_from_cache(
        self, _t: Tarballer, silent: bool = False
    ) -> tuple[set[Path], dict[str, set[str]]]:
        """
        Determine input files based on cache data:
        * If no cache data exists, recompile and store cache data.
        * If cache data exists and input files listed in it have their sha sums
          matching those of files in project — indicating no change in input
          files content, directly use these input files from project dir.
        * If cache data exists, but input files are missing or sha sums do not
          match up, recompile and update cache data.

        Returns: tuple of input dependency files paths, dict corresponding to
        package list
        """
        cache_path = Path(self.filehash_cache)
        try:
            c_path_msg = f"~/{cache_path.relative_to(Path.home())}"
        except ValueError:
            c_path_msg = str(cache_path)
        if not silent:
            log.info("Reading cache file: %s", c_path_msg)

        if cache_path.is_file():
            _deps: set[Path] = set()
            _pkgs: dict[str, set[str]] = {}
            if _tartex_hash_utils.check_file_hash(cache_path):
                if not silent:
                    log.info("No changes to input files, using cached data")
                with open(cache_path, "r") as cache:
                    _j = json.load(cache)
                    _deps.update([Path(f) for f in _j["input_files"].keys()])
                    _pkgs = _j["packages"]
                    missing: set[Path] = set()  # Missing files to discard

                    # Apart from obviously missing files from the set of _deps,
                    # anything in "streams" is automatically assumed missing
                    # since there is no way to have it restored and still
                    # verify its integrity. Resolved upon next cache update.
                    for _d in _deps.union([Path(_f) for _f in _j["streams"]]):
                        if not _d.is_file():
                            log.warning(
                                "Missing input file %s, try recompile ('-F')",
                                _d.name,
                            )
                            missing.add(_d)
                    _deps = _deps.difference(missing)
                _t.app_files(*_deps)
                if self.args.with_pdf:
                    self._add_pdf_stream(
                        self.main_file.with_suffix(".pdf"), _t, silent
                    )
                return _deps, _pkgs
            else:
                if not silent:
                    log.info("Dependencies missing or modified...")
        else:
            if not silent:
                log.info("Cache file missing...")

        return self.input_files_from_recompile(_t, cache_update=True)

    def _add_bib(self, _pkgs: dict[str, set[str]]):
        """
        Add bib and bst files to tarball; add bst filename to package list

        :_deps: set of files to be included in tarball
        :_pkgs: list of TeX packages that may be added to tarball as json file

        """
        bibs = set(
            [
                f
                for f in _tartex_tex_utils.bib_file(
                    self.main_file.with_suffix(".tex")
                )
                if f
            ]
        )

        for f in bibs:
            try:
                if f and re.match(r".bst", f.suffix):
                    _pkgs["Local"].add(f.as_posix())
            except Exception:
                pass

        return bibs

    def _add_user_files(self):
        """Add user specified extra files to tarball"""
        _files = set()
        for f in _tartex_tex_utils.add_files(
            self.add_files, self.main_file.parent
        ):
            f_relpath = f.relative_to(self.main_file.parent)
            _files.add(f_relpath)
            log.info("Add user specified file: %s", f_relpath)
        return _files

    def _add_pdf_stream(self, _file: Path, _t: Tarballer, silent: bool = False):
        """
        Add pdf as stream to Tarballer object

        :_file: path to pdf file
        :_t: Tarballer object to append pdf stream to
        :silent: suppress logs when `True` (bool)
        :returns: None

        """
        try:
            with open(_file, "rb") as f:
                self.pdf_stream = f.read()
                _t.app_stream(_file.name, self.pdf_stream)
        except FileNotFoundError:
            if not silent:
                log.warning(
                    "Skipping pdf not found: %s",
                    f"{_file.relative_to(self.main_file.parent)}",
                )
            self.args.with_pdf = False

    def _add_supplement_streams(self, _p: Path, _dep: set[Path], _t: Tarballer):
        """
        Add supplementary files as streams

        :_p: Path to stream
        :_t: Tarballer object to add `_p` to

        """
        for ext in _tartex_tex_utils.SUPP_REQ:
            supp_filename = self.main_file.with_suffix(f".{ext}")
            if app := self._missing_supp(
                self.main_file.with_suffix(f".{ext}"), _p, _dep
            ):
                self.req_supfiles[self.main_file.with_suffix(f".{ext}")] = app
                _t.app_stream(supp_filename.name, app)

    def tar_files(self):
        """
        Generates a tarball consisting of non-system input files needed to
        recompile your latex project. Main entry point to tartex cmdline app.
        """
        _git_cntxt = (
            git_checkout(self.GR.git_bin, self.GR.repo, self.GR.rev)
            if self.args.git_rev
            else nullcontext()
        )
        _pushd_src_dir = chdir(self.main_file.parent)
        if self.args.check or self.args.only_check:
            try:
                with _git_cntxt:
                    with _pushd_src_dir:
                        self.check_files(not self.args.only_check)
            except Exception:
                if not self.args.only_check:
                    log.critical("Check failed, no tarball will be generated")
                sys.exit(1)

        if self.args.only_check:
            return

        if self.tar_file_w_ext.exists() and not self.args.list:
            self.tar_file_w_ext, self.tar_ext = (
                _tartex_tar_utils.tar_name_conflict(
                    self.cwd,
                    self.main_file,
                    self.tar_file_w_ext,
                    self.args.overwrite,
                    self.tar_file_git_tag,
                )
            )
        tarball = Tarballer(self.cwd, self.main_file, self.tar_file_w_ext)
        try:
            with _git_cntxt:
                with _pushd_src_dir:
                    log.info(
                        "Switched to TeX file source dir: %s",
                        self.main_file.parent,
                    )
                    _ = self.input_files(tarball)
                    if self.args.list:
                        log.debug(
                            "Working in 'list' mode; no tarball will be produced"
                        )
                        tarball.print_list(self.args.summary)
                    else:
                        tarball.do_tar()
                        if self.args.summary:
                            _tartex_msg_utils.summary_msg(
                                tarball.num_objects,
                                self.tar_file_w_ext,
                                self.cwd,
                            )
                    log.info("Switching back to working dir: %s", self.cwd)
        except Exception:
            sys.exit(1)

    def check_files(self, silent: bool = False):
        """
        Checks if simulated target tarball will contain all files needed to
        recompile project (and any more).
        """

        log.debug("Working in `check` mode; no tarball will be produced")
        log.debug("Checking whether target tarball contents will recompile...")
        richprint(
            "[bright_black]Checking whether target tarball contents will recompile...[/]",
        )

        # Rich print indicators for missing or superfluous file messages
        INDI = {
            "req-miss": ":double_exclamation_mark-emoji: ",  # extra space req
            "not-need": ":warning-emoji: ",  # extra space req
            "perfect": ":heavy_check_mark-emoji: ",  # extra space req
            "chk-fail": ":cross_mark-emoji:",
            "chk-pass": ":ok_button-emoji:",
        }

        # The reference tarball `ref_tar` must contain the minimal number of
        # files/streams required to re-compile the project, ignoring any user
        # specified additionals. Thus, we determine the objects that will go
        # into this explicit recompilation (if latexmk fails at this stage,
        # the check is assumed to have failed — we cannot work around this) by
        # using `.input_files_from_recompile()`.
        #
        # When comparing a target tarfile against this ref, any additional
        # files in the former would raise a warning, but any missing file is an
        # error.
        #
        ref_tar = Tarballer(self.cwd, self.main_file, Path("ref.tar"))
        try:
            # passing `minimal=True` ensures tarballer obj includes only the
            # absolutely necessary files/streams as determined from a recompile
            deps, pkgs = self.input_files_from_recompile(
                ref_tar, minimal=True, silent=silent
            )
        except Exception as err:
            log.critical(
                "Latexmk failed to compile; check if all source files exist"
            )
            if not silent:
                richprint(
                    f"{INDI['req-miss']} Files need for compilation missing (deleted?)"
                )
            raise CheckFailError from err

        # dummy target including all user specified additionals/exclusions
        dummy_tar = Tarballer(self.cwd, self.main_file, Path("dummy.tar"))
        miss_msg = (
            "Files needed for compilation missing or excluded from tarball"
        )

        missing_supp = (
            set(
                [
                    self.main_file.with_suffix(f".{e}").relative_to(
                        self.main_file.parent
                    )
                    for e in _tartex_tex_utils.SUPP_REQ
                ]
            )
            if self.args.force_recompile
            else set()
        )
        # make sure supplementary file is actually needed
        missing_supp.intersection_update(ref_tar.objects())

        if not self.args.git_rev:
            self.input_files(dummy_tar, silent)

            # will return True if check fails
            chk_err = _check_err_missing(
                ref_tar,
                dummy_tar,
                indicator=INDI["req-miss"],
                supp_files=missing_supp,
            )
            if not silent:
                _ = _check_warn_extra(ref_tar, dummy_tar, INDI["not-need"])

        else:
            git_ref = self.args.git_rev or "HEAD"
            # Dummy target; will be populated by contents from `git ls-tree`
            # (plus user additionals)
            self.input_files(dummy_tar, silent)

            chk_err = _check_err_missing(
                ref_tar,
                dummy_tar,
                indicator=INDI["req-miss"],
                supp_files=missing_supp,
            )
            if not silent:
                _ = _check_warn_extra(ref_tar, dummy_tar, INDI["not-need"])

        if silent:
            if chk_err:
                log.debug("Check failed")
                richprint("[red]Check failed[/]")
            else:
                log.debug("Check succeeded")
                richprint("[green4]Check success[/]")
            if missing_supp:
                # log INFO if force recompiling, WARNING otherwise
                log.log(
                    log.INFO if self.args.force_recompile else log.WARNING,
                    "Missing supplementary file(s): %s",
                    ", ".join([str(_s) for _s in missing_supp]),
                )
        else:
            richprint("[green4]Files needed for compilation to be included:[/]")
            for f in ref_tar.objects().intersection(dummy_tar.objects()):
                richprint(INDI["perfect"], end=" ")
                print(f"{f!s}")
            else:
                print()

            if chk_err:
                richprint(f"{INDI['chk-fail']} [red]{miss_msg}[/]")
            else:
                log.info("All files needed for compilation are present")
                richprint(
                    f"{INDI['chk-pass']} [bold green4]All files needed for"
                    " compilation included in tarball"
                    f"{f' at git revision {git_ref}' if self.args.git_rev else ''}[/]"
                )

        if chk_err:
            raise CheckFailError(miss_msg)

    ############################
    ## CLASS HELPER FUNCTIONS ##
    ############################

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

    def _tar_filename(self):
        """
        Set member variables for tar output
        :returns: full tarball file name

        """
        _tar_ext = (
            self.tar_ext if self.tar_ext else _tartex_tar_utils.TAR_DEFAULT_COMP
        )
        # ...but overwrite TAR_EXT if a specific tar compression option passed
        if self.args.bzip2:
            _tar_ext = "bz2"
        if self.args.gzip:
            _tar_ext = "gz"
        if self.args.xz:
            _tar_ext = "xz"

        tar_file = (
            Path(f"{self.args.output}.tar")
            if self.args.output
            else Path(
                f"{self.main_file.stem}{self.tar_file_git_tag}"
            ).with_suffix(".tar")
        )

        # Note: if tar_file is already an abs path, 'foo/tar_file' simply returns 'tar_file'
        return self.cwd / tar_file.with_suffix(f".tar.{_tar_ext}")


###################################
## COMMAND LINE UTILITY FUNCTION ##
###################################
def make_tar():
    """Build tarball with command line arguments processed by argparse"""
    t = TarTeX(sys.argv[1:])
    t.tar_files()


if __name__ == "__main__":
    make_tar()
