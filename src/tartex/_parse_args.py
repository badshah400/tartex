# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""
Module that sets up argparse and returns parsed arguments from the cmdline
"""

import argparse
from pathlib import Path
from textwrap import wrap

from rich import print as richprint
from rich.markdown import Markdown
from rich.syntax import Syntax

from tartex.__about__ import __appname__ as APPNAME  # noqa: N812
from tartex.__about__ import __version__
from tartex._completion import (
    COMPFILE,
    BashCompletion,
    FishCompletion,
    ZshCompletion,
)

# Latexmk allowed compilers
LATEXMK_TEX = [
    "dvi",
    "lualatex",
    "luatex",
    "pdf",
    "pdflua",
    "ps",
    "xdv",
    "xelatex",
]


BASH_COMP_PATH = BashCompletion().install_dir.joinpath(f"{APPNAME}")
COMPLETIONS_GUIDE = f"""
Completions are currently supported for bash, fish, and zsh shells.
Please consider [contributing](https://github.com/badshah400/tartex) if you
would like completion for any other shell.

__Note__: XDG_DATA_HOME defaults to `~/.local/share`.

## Bash ##
The option `--bash-completion` will install bash completions for {APPNAME} to
the directory: $XDG_DATA_HOME/{COMPFILE["bash"]}.

Bash automatically searches this dir for completions, so completion for
tartex should work immediately after starting a new terminal session.  If it
does not, you may have to add the following lines to your
'~/.bashrc' file:

```bash
# Source {APPNAME} completion
source ~/{BASH_COMP_PATH.relative_to(Path.home())}
```

## Zsh ##
The option `--zsh-completion` will install a zsh completions file for {APPNAME}
to the directory: $XDG_DATA_HOME/{COMPFILE["zsh"].parent!s}.  It will also
print what to add to your .zshrc file to enable these completions.

## Fish ##
The option `--fish-completion` will install a fish completions file for
{APPNAME} to the directory: $XDG_DATA_HOME/{COMPFILE["fish"].parent!s}.

No further configuration should be needed. Simply start a new fish terminal et
voila!
"""

ZSH_GUIDE = f"""# Update fpath to include completions dir
# Note: Must be done before initialising compinit
fpath=(~/{ZshCompletion().install_dir.relative_to(Path.home())} $fpath)

# If the following two lines already appear in your .zshrc do not add them
# again, but move the fpath line above the 'autoload compinit' line
autoload -U compinit
compinit"""


class CompletionPrintAction(argparse.Action):
    """
    Defines CompletionAction for argparse which will print a completion syntax
    and exit
    """

    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None,  # noqa: A002
    ):
        """Initialise Action class"""
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    # Note that correct __call__ signature requires all positional args even if
    # they are not used in this method itself
    def __call__(self, parser, nsp, vals, opt_str=None):  # noqa: ARG002
        richprint(Markdown(COMPLETIONS_GUIDE))
        parser.exit()


class CompletionInstall(argparse.Action):
    """
    Defines CompletionAction for argparse which will print a completion syntax
    and exit
    """

    def __init__(
        self,
        option_strings,
        dest=argparse.SUPPRESS,
        default=argparse.SUPPRESS,
        help=None,  # noqa: A002
    ):
        """Initialise Action class"""
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    # Note that correct __call__ signature requires all positional args even if
    # they are not used in this method itself
    def __call__(self, parser, namespace, values, option_string=None):  # noqa
        parser.exit()


class BashCompletionInstall(CompletionInstall):
    """Completion install action for Bash shell"""

    def __call__(self, parser, namespace, values, option_strings=None):
        BashCompletion().install()
        super().__call__(parser, namespace, values, option_strings)
        parser.exit()


class FishCompletionInstall(CompletionInstall):
    """Completion install action for Fish shell"""

    def __call__(self, parser, namespace, values, option_strings=None):
        FishCompletion().install()
        super().__call__(parser, namespace, values, option_strings)
        parser.exit()


class ZshCompletionInstall(CompletionInstall):
    """Completion install action for Zsh shell"""

    def __call__(self, parser, namespace, values, option_strings=None):
        ZshCompletion().install()
        richprint(
            "\n"
            "Add the following to your [bold].zshrc[/] if not already present:"
        )
        richprint(Syntax(ZSH_GUIDE, "zsh"))
        super().__call__(parser, namespace, values, option_strings)
        parser.exit()


class GnuStyleHelpFormatter(argparse.HelpFormatter):
    """
    Format help string in GNU style, i.e.

    * `-s, --long           Help string for long`
      for an action that takes no argument
    * `-s, --long=LONG      Help string for long`
      for an action that requires an argument
    """

    def __init__(self, prog):
        """
        Initialise
        """
        argparse.HelpFormatter.__init__(
            self, prog, max_help_position=30, width=80
        )

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            (metavar,) = self._metavar_formatter(action, default)(1)
            return metavar

        parts = []

        # if the Optional doesn't take a value, format is:
        #    -s, --long
        if action.nargs == 0:
            parts.extend(action.option_strings)

        # if the Optional takes a value, format is:
        #    -s, --long=ARGS
        else:
            default = self._get_default_metavar_for_optional(action)
            args_string = self._format_args(action, default)
            for option_string in action.option_strings:
                if len(option_string.lstrip("-")) == 1:  # short form
                    parts.append(f"{option_string}")
                else:  # long form
                    parts.append(f"{option_string}={args_string}")

        return ", ".join(parts)

    def _split_lines(self, text, width):  # noqa: ARG002
        return wrap(text, width=52, break_on_hyphens=False)


def parse_args(args) -> argparse.Namespace:
    """Set up argparse options and parse input args accordingly"""
    parser = argparse.ArgumentParser(
        description=(
            "Build a tarball including all source files needed to compile your"
            f" LaTeX project (version {__version__})."
        ),
        formatter_class=GnuStyleHelpFormatter,
        usage="%(prog)s [OPTIONS] FILENAME",
        add_help=False,
    )

    parser.add_argument(
        "fname",
        metavar="FILENAME",
        type=Path,
        help="input file name [.fls|.tex] (with/without extension)",
    )

    general_opts = parser.add_argument_group("common options")
    general_opts.add_argument(
        "-h",
        "--help",
        help="show this help message and exit",
        action="help",
    )

    general_opts.add_argument(
        "-V",
        "--version",
        help="print %(prog)s version and exit",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    general_opts.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Check if tarball has all files needed for compiling"
    )

    general_opts.add_argument(
        "-C",
        "--only-check",
        action="store_true",
        help="Only check and print detailed report; no tarball"
    )

    general_opts.add_argument(
        "-g",
        "--git-rev",
        metavar="REV",
        type=str,
        nargs="?",
        help=("add git tree files at revision REV (default: HEAD)"),
        default="",  # used when `-g`/`--git-rev` is not used
        const="HEAD",  # used when `-g`/`--git-rev` is used with empty param
    )

    general_opts.add_argument(
        "-l",
        "--list",
        "--dry-run",
        dest="list",
        action="store_true",
        help="print list of files to include and quit",
    )

    general_opts.add_argument(
        "-o",
        "--output",
        metavar="NAME[.EXT]",
        type=Path,
        help=(
            "output tar filename; 'EXT' sets re-compression mode,"
            " if one of 'bz2', 'gz' (default), or 'xz'"
        ),
    )

    general_opts.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite output tarball if necessary",
    )

    general_opts.add_argument(
        "-p",
        "--packages",
        action="store_true",
        help="add used (La)TeX package names as json file",
    )

    general_opts.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="print a summary at the end",
    )

    general_opts.add_argument(
        "-v",
        "--verbose",
        help="increase log verbosity (-v, -vv, etc.)",
        action="count",
        default=0,
    )

    # File inclusion, exclusion options
    file_opts = parser.add_argument_group(
        "options for additional file inclusion/exclusion in tar"
    )

    file_opts.add_argument(
        "-a",
        "--add",
        metavar="\"PATTERNs\"",
        type=str,
        help=(
            "include additional files matching glob PATTERN;"
            " separate multiple PATTERNs using commas"
        ),
    )

    file_opts.add_argument(
        "-b",
        "--bib",
        action="store_true",
        help="find and add bib file to tarball",
    )

    file_opts.add_argument(
        "--with-pdf",
        action="store_true",
        help="add existing/generated final output PDF",
    )

    file_opts.add_argument(
        "-x",
        "--excl",
        metavar="\"PATTERNs\"",
        type=str,
        help="exclude file names matching PATTERNS",
    )

    # Latexmk options
    latexmk_opts = parser.add_argument_group(
        "options for latexmk processing (ignored for 'git-rev')"
    )
    latexmk_opts.add_argument(
        "-F",
        "--force-recompile",
        action="store_true",
        help="force (La)TeX re-compile; cache use/update disabled",
    )

    latexmk_opts.add_argument(
        "--latexmk-tex",
        metavar="TEXMODE",
        choices=LATEXMK_TEX,
        default=None,
        help=(
            "force latexmk processing mode;"
            f" TEXMODE is one of: {', '.join(LATEXMK_TEX)}"
        ),
    )

    # Tar recompress options
    tar_opts_grp = parser.add_argument_group(
        "options for tar re-compression (mutually conflicting); over-rides .EXT in '-o'"
    )
    tar_opts = tar_opts_grp.add_mutually_exclusive_group()

    def cmp_str(cmp, ext):
        return f"{cmp} (.{ext}) re-compression"

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

    shcomp_opts = parser.add_argument_group("options for shell TAB completion")
    shcomp_opts.add_argument(
        "--completion",
        help="print shell completion guides for %(prog)s",
        action=CompletionPrintAction,
    )

    shcomp_opts.add_argument(
        "--bash-completions",
        help="install bash completions for %(prog)s",
        action=BashCompletionInstall,
    )

    shcomp_opts.add_argument(
        "--fish-completions",
        help="install fish completions for %(prog)s",
        action=FishCompletionInstall,
    )

    shcomp_opts.add_argument(
        "--zsh-completions",
        help="install zsh completions for %(prog)s",
        action=ZshCompletionInstall,
    )

    return parser.parse_args(args)
