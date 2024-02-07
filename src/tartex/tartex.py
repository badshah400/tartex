# vim: set ai et ts=4 sw=4 tw=80:
"""tartex DocString"""

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile as tar
from pathlib import Path
from tempfile import TemporaryDirectory

from . import __about__

# Match only lines beginning with INPUT
INPUT_RE = re.compile(r"^INPUT")

# Auxilliary file extensions to ignore
AUXFILES = [".aux", ".toc", ".out", ".fls", ".fdb_latexmk", ".log", ".blg", ".idx"]

# Get version
VERSION  = __about__.__version__

def parse_args(args):
    """Set up argparse options and parse input args accordingly"""
    parser = argparse.ArgumentParser(
        description="Build a tarball including all source"
        " files needed to compile your LaTeX project"
        f" (version {VERSION})."
    )

    parser.add_argument(
        "fname", type=str, help="Input file name (.tex or .fls) (mandatory)"
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
        help="Display file names added to tarball",
        action="store_true",
    )

    parser.add_argument(
        "-x",
        "--excl",
        type=str,
        default=[],
        help="Comma separated list of files (wildcards allowed!) to exclude "
        "(loc relative to main TeX file)",
    )

    return parser.parse_args(args)


class TarTeX:
    """Class to help build  a tarball including all source files needed to
    re-compile your LaTeX project."
    """

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
        self.add_files = self.args.add.split(",") if len(self.args.add) > 0 else []
        excludes = self.args.excl.split(",") if len(self.args.excl) > 0 else []
        excl_lists = (self.main_file.parent.glob(f"{L}") for L in excludes)

        self.excl_files = [
            f.relative_to(self.main_file.parent).as_posix()
            for L in excl_lists
            for f in L
        ]

    def add_user_files(self):
        """Return list of additional user specified/globbed file paths,
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
        """Returns non-system input files needed to compile the main tex file.
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
        if self.args.list:
            print(f"Summary: {nfiles} files to include.")
        else:
            print(f"Summary: {tarname} generated with {nfiles} files.")

    def tar_files(self, ext="gz"):
        """Generates a tarball consisting of non-system input files needed to
        recompile your latex project.
        """
        self.check_main_file_exists()
        full_tar_name = Path(f"{self.tar_file}.{ext}")
        if full_tar_name.exists() and not self.args.list:
            owr = input(
                "Warning: A tar file with the same already exists.\n"
                "What would you like to do "
                "([o]verwrite/[c]hoose new name/[Q]uit)? "
            )
            if owr.lower() in ["", "q"]:
                sys.exit("Not overwriting existing tar file; quitting.")
            elif owr.lower() == "c":
                new_name = input("Enter new name for tar file: ")
                if Path(new_name).with_suffix(f".tar.{ext}").resolve() == full_tar_name:
                    sys.exit(
                        "New name entered is also the same as existing tar file"
                        " name; quitting."
                    )
                else:
                    full_tar_name = Path(new_name).with_suffix(f".tar.{ext}")
            elif owr.lower() == "o":
                pass
            else:
                sys.exit("Invalid response; quitting.")

        wdir = self.main_file.resolve().parent
        os.chdir(wdir)
        flist = self.input_files()
        if self.args.list:
            for i, f in enumerate(flist):
                print(f"{i+1:{int(math.log10(len(flist)))+1}}. {f}")
        else:
            with tar.open(full_tar_name, mode=f"w:{ext}") as f:
                for dep in flist:
                    if self.args.verbose:
                        print(dep)
                    f.add(dep)
        os.chdir(self.cwd)
        if self.args.summary:
            self.summary_msg(full_tar_name.relative_to(self.cwd), len(flist))

    def check_main_file_exists(self):
        """Check for the existence of the main tex/fls file."""
        if not Path(self.main_file).exists():
            print(f"Error: File not found - {self.main_file}")
            sys.exit(-1)


def make_tar(ext="gz"):
    """Build the tarball with command line arguments processed by argparse"""
    t = TarTeX(sys.argv[1:])
    t.tar_files(ext)


if __name__ == "__main__":
    make_tar()
