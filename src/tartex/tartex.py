# vim: set ai et ts=4 sw=4 tw=80:
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
from pathlib import Path
from tempfile import TemporaryDirectory

from io import BytesIO

from . import __about__

# Match only lines beginning with INPUT
INPUT_RE = re.compile(r"^INPUT")

# Auxilliary file extensions to ignore
AUXFILES = [".aux", ".toc", ".out", ".fls", ".fdb_latexmk", ".log", ".blg", ".idx"]

# Get version
VERSION = __about__.__version__


def parse_args(args):
    """Set up argparse options and parse input args accordingly"""
    parser = argparse.ArgumentParser(
        description="Build a tarball including all"
        " source files needed to compile your"
        f" LaTeX project (version {VERSION})."
    )

    parser.add_argument(
        "fname",
        metavar="filename",
        type=str,
        help="Input file name (.tex or .fls)"
    )

    parser.add_argument(
        "-a",
        "--add",
        type=str,
        default=[],
        help="Comma separated list of additional files (wildcards allowed!) "
        "to include (loc relative to main TeX file)",
    )

    parser.add_argument(
        "-b", "--bib", help="find and add bib file to tarball ", action="store_true"
    )

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="Print a list of files to include and quit (no tarball generated)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Name of output tar.gz file (w/o the .tar.gz extension)",
    )

    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Print a summary at the end",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Print file names added to tarball",
        action="store_true",
    )

    parser.add_argument(
        "-x",
        "--excl",
        type=str,
        default=[],
        help="Comma separated list of files (wildcards allowed!) to exclude "
        "(loc relative to main TeX file)"
    )

    # Tar recompress options
    tar_opts = parser.add_mutually_exclusive_group()

    tar_opts.add_argument(
        "-j",
        "--bzip2",
        action="store_true",
        help="Compress tar with bzip2, generating .tar.bz2 file"
    )

    tar_opts.add_argument(
        "-J",
        "--xz",
        action="store_true",
        help="Compress tar with xz, generating .tar.xz file"
    )

    tar_opts.add_argument(
        "-z",
        "--gzip",
        action="store_true",
        help="Compress tar with gzip, generating .tar.gz file (default)"
    )

    parser.add_argument(
        "-V",
        "--version",
        help="Print %(prog)s version",
        action="version",
        version=f"%(prog)s {VERSION}"
    )

    return parser.parse_args(args)


class TarTeX:
    """
    Class to help build  a tarball including all source files needed to
    re-compile your LaTeX project."
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, args):
        self.cwd = Path(os.getcwd())
        self.args = parse_args(args)
        self.main_file = Path(self.args.fname)
        tar_base = (
            Path(self.args.output).with_suffix(".tar")
            if self.args.output
            else Path(self.main_file.stem).with_suffix(".tar")
        )
        self.tar_file = self.cwd / tar_base
        self.tar_ext  = "gz"

        if self.args.bzip2:
            self.tar_ext = "bz2"
        if self.args.gzip:
            self.tar_ext = "gz"
        if self.args.xz:
            self.tar_ext = "xz"

        self.bbl = None
        self.add_files = self.args.add.split(",") if len(self.args.add) > 0 else []
        excludes = self.args.excl.split(",") if len(self.args.excl) > 0 else []
        excl_lists = (self.main_file.parent.glob(f"{L}") for L in excludes)

        self.excl_files = [
            f.relative_to(self.main_file.parent).as_posix()
            for L in excl_lists
            for f in L
        ]

        # If .bbl is missing in source dir, then it is not in self.excl_files
        # even if the user passes a matching wildcard to exclude it with "-x".
        # Handle this case
        for glb in excludes:
            main_bbl = self.main_file.with_suffix(".bbl")
            if fnmatch.fnmatch(main_bbl.name, glb):
                self.excl_files.append(main_bbl)

    def add_user_files(self):
        """
        Return list of additional user specified/globbed file paths,
        if they exist
        """
        lof = []
        for fpatt in self.add_files:
            afiles = Path(".").glob(fpatt)
            for af in afiles:
                if not af.resolve().exists():
                    print(
                        f"Warning: File {af.name} marked for addition not found, "
                        "skipping..."
                    )
                    continue
                lof.append(af.as_posix())

        return lof

    def bib_file(self):
        """Return relative path to bib file"""
        bibre = re.compile(r"^\\bibliography\{.*\}")
        bibstr = None
        texf = self.main_file.with_suffix(".tex")
        with open(texf, encoding="utf-8") as f:
            for line in f:
                # print(line)
                m = bibre.search(line)
                if m:
                    bibstr = m.group()
                    break

        if bibstr:
            bibstr = re.sub(r"^\\bibliography\{", "", bibstr).rstrip("}")
            bibstr += ".bib" if bibstr.split(".")[-1] != ".bib" else ""

        return Path(bibstr)

    def input_files(self):
        """
        Returns non-system input files needed to compile the main tex file.
        Note that this will try to compile the main tex file using `latexmk` if
        it cannot find the fls file in the same dir.
        """
        deps = []
        with TemporaryDirectory() as compile_dir:
            fls_name = self.main_file.with_suffix(".fls")
            fls_path = Path(".") / fls_name
            if not Path(fls_name).exists():
                # Generate flx file from tex file by running latexmk
                latexmk_bin = shutil.which("latexmk")

                try:
                    subprocess.run(
                        [
                            latexmk_bin,
                            "-f",
                            "-pdf",
                            "-cd",
                            f"-outdir={compile_dir}",
                            "-interaction=nonstopmode",
                            self.main_file.stem,
                        ],
                        capture_output=True,
                        encoding="utf-8",
                        check=True,
                    )
                except OSError as err:
                    print(f"Error: {err.strerror}")
                    sys.exit(1)
                except subprocess.CalledProcessError as err:
                    print(f"Error: {err.cmd[0]} failed with the following output:")
                    print(err.stdout)
                    sys.exit(2)

                fls_path = Path(compile_dir) / f"{self.main_file.stem}.fls"

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

                bbl_file = self.main_file.with_suffix(".bbl")
                # Handle missing bbl file from orig dir, if present in fls_path
                if (
                    bbl_file not in deps  # bbl file not in source dir
                    and
                    (Path(compile_dir) / bbl_file.name).exists() # Implies it's req
                    and
                    bbl_file not in self.excl_files # Not explicitly excluded
                ):
                    self.bbl = (Path(compile_dir) / bbl_file.name).read_bytes()

        if self.args.bib:
            deps.append(self.bib_file().as_posix())

        if self.add_files:
            for f in self.add_user_files():
                if f in deps:
                    print(
                        f"Warning: Manually included file {f} already "
                        "marked for inclusion, skipping..."
                    )
                    continue
                deps.append(f)

        return deps

    def summary_msg(self, tarname, nfiles):
        """Return summary msg to print at end of run"""
        num_files = nfiles + (1 if self.bbl else  0)
        if self.args.list:
            print(f"Summary: {num_files} files to include.")
        else:
            print(f"Summary: {tarname} generated with {num_files} files.")

    def tar_files(self):
        """Generates a tarball consisting of non-system input files needed to
        recompile your latex project.
        """
        self.check_main_file_exists()
        full_tar_name = Path(f"{self.tar_file}.{self.tar_ext}")

        if full_tar_name.exists() and not self.args.list:
            if(p := self._tar_name_conflict(full_tar_name, self.tar_ext)):
                full_tar_name = p

        wdir = self.main_file.resolve().parent
        os.chdir(wdir)
        flist = self.input_files()
        if self.args.list:
            idx_width = int(math.log10(len(flist))) + 1
            for i, f in enumerate(flist):
                print(f"{i+1:{idx_width}}. {f}")
            if self.bbl:
                print(f"{'*':>{idx_width}}  {self.main_file.with_suffix('.bbl')}")
        else:
            with tar.open(full_tar_name, mode=f"w:{self.tar_ext}") as f:
                for dep in flist:
                    f.add(dep)
                if self.bbl:
                    tinfo = f.tarinfo(self.main_file.with_suffix(".bbl").name)
                    tinfo.size = len(self.bbl)
                    tinfo.mtime = int(time.time())
                    f.addfile(tinfo, BytesIO(self.bbl))
                if self.args.verbose:
                    print('\n'.join(f.getnames()))

        os.chdir(self.cwd)
        if self.args.summary:
            self.summary_msg(full_tar_name.resolve().relative_to(self.cwd), len(flist))

    def _tar_name_conflict(self, tpath, ext):
        owr = input(
                "Warning: A tar file with the same already exists.\n"
                "What would you like to do "
                "([o]verwrite/[c]hoose new name/[Q]uit)? "
            )
        if owr.lower() in ["", "q"]:
            sys.exit("Not overwriting existing tar file; quitting.")
        elif owr.lower() == "c":
            new_name = input("Enter new name for tar file: ")
            new_path = Path(new_name).with_suffix(f".tar.{ext}").resolve()
            if new_path == tpath:
                sys.exit(
                    "New name entered is also the same as existing tar file"
                    " name.\nQuitting."
                )
            elif new_path.exists():
                sys.exit("Another file with the same name also"
                         " exists.\nQuitting.")
            else:
                full_name = Path(new_name).with_suffix(f".tar.{ext}")
                return full_name
        elif owr.lower() == "o":
            return None
        else:
            sys.exit("Invalid response; quitting.")

    def check_main_file_exists(self):
        """Check for the existence of the main tex/fls file."""
        if not Path(self.main_file).exists():
            print(f"Error: File not found - {self.main_file}")
            sys.exit(-1)


def make_tar():
    """Build tarball with command line arguments processed by argparse"""
    t = TarTeX(sys.argv[1:])
    t.tar_files()


if __name__ == "__main__":
    make_tar()
