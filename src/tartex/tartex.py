# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""tartex module"""

import argparse
import fnmatch
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile as tar
import time
from contextlib import suppress
from io import BytesIO
import logging as log
from pathlib import Path
from tempfile import TemporaryDirectory

from tartex import __about__

# Match only lines beginning with INPUT
INPUT_RE = re.compile(r"^INPUT")

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

# Latexmk allowed compilers
LATEXMK_TEX = ["dvi", "luatex", "lualatex", "pdf", "pdflua", "ps", "xdv", "xelatex"]

# Supplementary files that are usually required as part of tarball
SUPP_REQ = ["bbl", "ind"]

# Allowed tar extensions
TAR_EXT = ["bz2", "gz", "xz"]

# Default compression
TAR_DEFAULT_COMP = "gz"

# Get version
VERSION = __about__.__version__


def parse_args(args):
    """Set up argparse options and parse input args accordingly"""
    parser = argparse.ArgumentParser(
        description="Build a tarball including all"
        " source files needed to compile your"
        f" LaTeX project (version {VERSION}).",
        usage="%(prog)s [options] filename",
    )

    parser.add_argument(
        "fname",
        metavar="filename",
        type=str,
        help="Input file name (with .tex or .fls suffix)",
    )

    parser.add_argument(
        "-a",
        "--add",
        type=str,
        help="Comma separated list of additional files (wildcards allowed!)"
             " to include (loc relative to main TeX file)",
    )

    parser.add_argument(
        "-b",
        "--bib",
        action="store_true",
        help="find and add bib file to tarball"
    )

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="Print a list of files to include and quit (no tarball generated)"
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Name of output tar file (suffix can determine tar compression)"
    )

    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Print a summary at the end"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Print file names added to tarball",
        action="count",
        default=0,
    )

    parser.add_argument(
        "-x",
        "--excl",
        type=str,
        help="Comma separated list of files (wildcards allowed!) to exclude"
             " (loc relative to main TeX file)"
    )

    # Latexmk options
    latexmk_opts = parser.add_argument_group("Options for latexmk processing")
    latexmk_opts.add_argument(
        "--latexmk_tex",
        choices=LATEXMK_TEX,
        default=None,
        help="Force TeX processing mode used by latexmk",
    )

    latexmk_opts.add_argument(
        "-F",
        "--force_recompile",
        action="store_true",
        help="Force recompilation even if .fls exists",
    )

    # Tar recompress options
    tar_opts = parser.add_mutually_exclusive_group()

    def cmp_str(cmp, ext):
        return(f"{cmp} (.tar.{ext}) compression"
               " (overrides OUTPUT ext if needed)"
              )

    tar_opts.add_argument(
        "-j",
        "--bzip2",
        action="store_true",
        help=cmp_str("bzip2", "bz2"),
    )

    tar_opts.add_argument(
        "-J",
        "--xz",
        action="store_true",
        help=cmp_str("lzma", "xz"),
    )

    tar_opts.add_argument(
        "-z",
        "--gzip",
        action="store_true",
        help=cmp_str("gzip", "gz"),
    )

    parser.add_argument(
        "-V",
        "--version",
        help="Print %(prog)s version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser.parse_args(args)


def strip_tarext(filename):
    """Strip '.tar(.EXT)' from filename"""
    basename = Path(filename)
    if basename.suffix.lstrip(".") in TAR_EXT:
        basename = basename.with_suffix("")
    if basename.suffix == ".tar":
        basename = basename.with_suffix("")
    return basename


def _full_if_not_rel_path(src, dest):
    p = Path(src).resolve()
    with suppress(ValueError):
        p = p.relative_to(dest)
    if p.is_absolute(): # At this stage p is only absolute if it cannot be
                        # resolved related to dest
        log.debug(
            "Cannot resolve %s relative to %s, will use full path",
            src.as_posix(), dest.as_posix()
        )
    # The assignment and return are both necessary in this case
    return p  # noqa: RET504


class TarTeX:
    """
    Class to help build  a tarball including all source files needed to
    re-compile your LaTeX project."
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, args):
        self.args = parse_args(args)
        log.basicConfig(
            format="[%(levelname)s] %(message)s",
            level=((log.INFO // self.args.verbose)
                   if self.args.verbose > 0 else log.WARN)
        )
        self.cwd = Path(os.getcwd())
        self.main_file = Path(self.args.fname).resolve()
        if self.main_file.suffix not in [".fls", ".tex"]:
            sys.exit("Error: Source filename must be .tex or .fls\nQuitting")

        # Set default tar extension...
        self.tar_ext = TAR_DEFAULT_COMP
        # ..but use specified output's TAR_EXT extension if any...
        if out := self.args.output:
            if (oex := out.split(".")[-1]) in TAR_EXT:
                self.tar_ext = oex
            else:
                # Check if output is an existing dir
                if Path(out).is_dir():
                    log.debug("%s is an exiting dir", out)
                    self.args.output = (
                        Path(out).joinpath(
                            self.main_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}").name
                        ).as_posix()
                    )

        # ...but overwrite TAR_EXT if tar compression option passed
        if self.args.bzip2:
            self.tar_ext = "bz2"
        if self.args.gzip:
            self.tar_ext = "gz"
        if self.args.xz:
            self.tar_ext = "xz"

        tar_base = (
            strip_tarext(self.args.output).with_suffix(".tar").expanduser()
            if self.args.output
            else Path(self.main_file.stem).with_suffix(".tar")
        )
        self.tar_file = self.cwd / tar_base
        log.debug(
            "Output tarball '%s' will be generated",
            self.tar_file.with_suffix(f".tar.{self.tar_ext}")
        )

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
                    for f in [self.main_file.with_suffix(f".{g}")
                              for g in SUPP_REQ]
                    if fnmatch.fnmatch(f.name, glb)
                ]
            )

        if self.excl_files:
            log.debug(" ".join(excl_lists))
            log.info(
                "List of excluded files: %s",
                ", ".join([x.as_posix() for x in self.excl_files]))

        self.force_tex = self.args.latexmk_tex
        if not self.force_tex:
            # If force_tex is not set by user options,
            # set to ps if source dir contains ps/eps files
            # or to pdf otherwise
            src_ps = [str(p)
                      for ext in ["eps", "ps"]
                      for p in self.main_file.parent.glob(f"**/*.{ext}")]
            self.force_tex = "ps" if src_ps else "pdf"
            log.info(
                "Latexmk will use %slatex for processing, if needed",
                self.force_tex
            )

        self.recompile = self.args.force_recompile

    def add_user_files(self):
        """
        Return list of additional user specified/globbed file paths,
        if they exist
        """
        lof = []
        for fpatt in self.add_files:
            afiles = list(self.main_file.parent.glob(fpatt))
            if not afiles:
                log.warning(
                    "No match corresponding to user specified pattern '%s' for"
                    " additional files",
                    fpatt
                )
                continue
            lof.extend(afiles)

        return lof

    def bib_file(self):
        """Return relative path to bib file"""
        bibre = re.compile(r"^\\bibliography\{.*\}")
        bibstr = None
        texf = self.main_file.with_suffix(".tex")
        with open(texf, encoding="utf-8") as f:
            for line in f:
                m = bibre.search(line)
                if m:
                    bibstr = m.group()
                    break

        if bibstr:
            bibstr = re.sub(r"^\\bibliography\{", "", bibstr).rstrip("}")
            bibstr += ".bib" if bibstr.split(".")[-1] != ".bib" else ""

        return Path(bibstr) if bibstr else None

    def input_files(self):
        """
        Returns non-system input files needed to compile the main tex file.
        Note that this will try to compile the main tex file using `latexmk` if
        it cannot find the fls file in the same dir.
        """
        deps = []
        with TemporaryDirectory() as compile_dir:
            fls_path = self.main_file.with_suffix(".fls")
            if not fls_path.exists() or self.recompile:
                log.info(
                    "%s.fls file not found in %s",
                    self.main_file.stem,
                    self.main_file.parent
                )
                log.info("Recompiling LaTeX project in %s", compile_dir)
                # Generate flx file from tex file by running latexmk
                latexmk_cmd = [
                    shutil.which("latexmk"),
                    f"-{self.force_tex}",
                    "-f",
                    "-cd",
                    f"-outdir={compile_dir}",
                    "-interaction=nonstopmode",
                    self.main_file.name,
                ]
                try:
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
                    log.critical("Error: %s failed with the following output:\n"
                                 "%s", err.cmd[0], err.stdout)
                    sys.exit(1)

                log.info(
                    "LaTeX project successfully compiled with: %s",
                    ' '.join(latexmk_cmd)
                )
                fls_path = Path(compile_dir) / f"{self.main_file.stem}.fls"
                log.debug("%s generated", fls_path.as_posix())

            with open(fls_path, encoding="utf-8") as f:
                for line in f:
                    if INPUT_RE.match(line):
                        p = Path(line.split()[-1])
                        if (
                            not p.is_absolute()
                            and (p.as_posix() not in deps)
                            and (p.as_posix() not in self.excl_files)
                            and (p.suffix not in AUXFILES)
                        ):
                            deps.append(p.as_posix())
                            log.info("Add file: %s", p.as_posix())

                def _missing_supp(fpath):
                    """ Handle missing supplemetary file from orig dir, if req

                    :fpath: may be one of .bib or .ind file paths
                    :returns: path of corresponding file from compile_dir

                    """
                    if (
                        fpath not in deps  # bbl file not in source dir
                        and (Path(compile_dir) / fpath.name).exists()  # Implies it's req
                        and fpath not in self.excl_files  # Not explicitly excluded
                    ):
                        log.debug(
                            "Required file '%s' not in source dir", fpath.name
                        )
                        log.info(
                            "Add contents as BytesIO: %s",
                            Path(compile_dir) / fpath.name
                        )
                        return (Path(compile_dir) / fpath.name).read_bytes()

                    return None

                for ext in SUPP_REQ:
                    if (app :=_missing_supp(self.main_file.with_suffix(f".{ext}"))):
                        self.req_supfiles[self.main_file.with_suffix(f".{ext}")] = app

        if self.args.bib and (bib := self.bib_file()):
            deps.append(bib.as_posix())
            log.info("Add file: %s", deps[-1])

        if self.add_files:
            for f in self.add_user_files():
                f_relpath_str = f.relative_to(self.main_file.parent).as_posix()
                if f_relpath_str in deps:
                    log.warning(
                        "Manually included file %s already added",
                        f_relpath_str
                    )
                    continue
                deps.append(f_relpath_str)
                log.info("Add user specified file: %s", f_relpath_str)

        return deps

    def summary_msg(self, tarname, nfiles):
        """Return summary msg to print at end of run"""
        num_files = nfiles + len(self.req_supfiles)
        num_tag   = f"{num_files} file" + ("s" if num_files > 1 else "")
        if self.args.list:
            print(f"Summary: {num_tag} to include.")
        else:
            print(f"Summary: {tarname} generated with {num_tag}.")

    def tar_files(self):
        """Generates a tarball consisting of non-system input files needed to
        recompile your latex project.
        """
        self.check_main_file_exists()
        full_tar_name = Path(f"{self.tar_file}.{self.tar_ext}")

        if (
            full_tar_name.exists()
            and not self.args.list
            and (p := self._tar_name_conflict(full_tar_name))
        ):
            full_tar_name = p

        wdir = self.main_file.resolve().parent
        os.chdir(wdir)
        log.debug("Switching working dir to %s", wdir.as_posix())
        flist = self.input_files()
        if self.args.list:
            idx_width = int(math.log10(len(flist))) + 1
            for i, f in enumerate(flist):
                print(f"{i+1:{idx_width}}. {f}")
            for r in self.req_supfiles:
                print(f"{'*':>{idx_width + 1}}"
                      f" {r.name}")
        else:
            with tar.open(full_tar_name, mode=f"w:{self.tar_ext}") as f:
                for dep in flist:
                    f.add(dep)

                for fpath, byt in self.req_supfiles.items():
                    tinfo = f.tarinfo(fpath.name)
                    tinfo.size = len(byt)
                    tinfo.mtime = int(time.time())
                    # Copy user/group names from main.tex file
                    tinfo.uname = f.getmember(self.main_file.name).uname
                    tinfo.gname = f.getmember(self.main_file.name).gname

                    f.addfile(tinfo, BytesIO(byt))

        os.chdir(self.cwd)
        log.debug("Reset working dir to %s", os.getcwd())
        if self.args.summary:
            self.summary_msg(_full_if_not_rel_path(full_tar_name, self.cwd), len(flist))

    def _tar_name_conflict(self, tpath):
        print(
            "A tar file with the same name"
            f" [{_full_if_not_rel_path(tpath, self.cwd)}] already exists."
        )

        owr = input(
            "What would you like to do ([o]verwrite/[c]hoose new name/[Q]uit)? "
        )
        if owr.lower() in ["", "q"]:
            sys.exit("Not overwriting existing tar file\nQuitting")
        elif owr.lower() == "c":
            new_name = input("Enter new name for tar file: ")
            if (new_ext := new_name.split(".")[-1]) in TAR_EXT:
                self.tar_ext = new_ext
            # If new file is a plain file name, interpret w.r.t. output dir
            if self.args.output and (str(Path(new_name)) == Path(new_name).name):
                new_name = Path(self.args.output).parent.joinpath(new_name).as_posix()
            new_path = (
                strip_tarext(new_name)
                .with_suffix(f".tar.{self.tar_ext}")
                .expanduser()
                .resolve()
            )
            if new_path == tpath:
                sys.exit(
                    "Error: New name entered is also the same as existing tar"
                    " file name\nQuitting"
                )
            elif new_path.exists():
                sys.exit(
                    "Error: A tar file with the same name also"
                    " exists\nQuitting"
                )
            else:
                log.info("Tar file %s will be generated", new_path.as_posix())
                return new_path
        elif owr.lower() == "o":
            return None
        else:
            sys.exit("Error: Invalid response\nQuitting.")

    def check_main_file_exists(self):
        """Check for the existence of the main tex/fls file."""
        if not Path(self.main_file).exists():
            log.critical("File not found - %s", self.main_file)
            sys.exit(1)


def make_tar():
    """Build tarball with command line arguments processed by argparse"""
    t = TarTeX(sys.argv[1:])
    t.tar_files()


if __name__ == "__main__":
    make_tar()
