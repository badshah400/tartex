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

from tartex.__about__ import __version__
from tartex._completion import BashCompletion, ZshCompletion

# Latexmk allowed compilers
LATEXMK_TEX = [
    "dvi",
    "luatex",
    "lualatex",
    "pdf",
    "pdflua",
    "ps",
    "xdv",
    "xelatex",
]


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
        help=None,
    ):
        """Initialise Action class"""
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print("Completion is currently supported for bash and zsh shells.")
        print(
            "Please consider contributing if you would like completion for"
            " any other shell"
        )
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
        help=None,
    ):
        """Initialise Action class"""
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit()


class BashCompletionInstall(CompletionInstall):

    """Completion install action for Bash shell"""

    def __call__(self, parser, namespace, values, option_strings=None):
        BashCompletion().install()
        super().__call__(parser, namespace, values, option_strings)


class ZshCompletionInstall(CompletionInstall):

    """Completion install action for Zsh shell"""

    def __call__(self, parser, namespace, values, option_strings=None):
        ZshCompletion().install()
        print(
            "\nAdd the following to your .zshrc if not already present:"
            "\n-----------------------------------------------------------"
        )
        print(
            "# Update fpath to include completions dir\n"
            "# Note: Must be done before initialising compinit\n"
            "fpath"
            f"=(~/{ZshCompletion().install_dir.relative_to(Path.home())}"
            " $fpath)\n"
            "\n"
            "# If the following two lines already appear in your .zshrc\n"
            "# do not add them again, but move the fpath line above the\n"
            "# 'autoload compinit' line\n"
            "autoload -U compinit\n"
            "compinit"
            "\n-----------------------------------------------------------\n"
        )
        super().__call__(parser, namespace, values, option_strings)


class GnuStyleHelpFormatter(argparse.HelpFormatter):

    """
    Format help string in GNU style, i.e.

    * `-s, --long           Help string for long`
      for an action that takes no argument
    * `-s, --long=LONG      Help string for long`
      for an action that requires an argument
    """

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


def parse_args(args):
    """Set up argparse options and parse input args accordingly"""
    parser = argparse.ArgumentParser(
        description=(
            "Build a tarball including all source files needed to compile your"
            f" LaTeX project (version {__version__})."
        ),
        formatter_class=GnuStyleHelpFormatter,
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
        metavar="PATTERNS",
        type=str,
        help=(
            "Comma separated list of file name PATTERNS to additionally"
            " include (relative to main TeX file)"
        ),
    )

    parser.add_argument(
        "-b",
        "--bib",
        action="store_true",
        help="find and add bib file to tarball",
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
        metavar="NAME[.SUF]",
        type=str,
        help="Name of output tar (.SUF, if any, may set tar compression)",
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
        action="count",
        default=0,
    )

    parser.add_argument(
        "-x",
        "--excl",
        metavar="PATTERNS",
        type=str,
        help=(
            "Comma separated list of file name PATTERNS to exclude"
            " (relative to main TeX file)"
        ),
    )

    # Latexmk options
    latexmk_opts = parser.add_argument_group("Options for latexmk processing")
    latexmk_opts.add_argument(
        "--latexmk-tex",
        metavar="TEXMODE",
        choices=LATEXMK_TEX,
        default=None,
        help="Force TeX processing mode used by latexmk (TEXMODE must be one"
        f" of: {', '.join(LATEXMK_TEX)})",
    )

    latexmk_opts.add_argument(
        "-F",
        "--force-recompile",
        action="store_true",
        help="Force recompilation even if .fls exists",
    )

    # Tar recompress options
    tar_opts = parser.add_mutually_exclusive_group()

    def cmp_str(cmp, ext):
        return (
            f"{cmp} (.tar.{ext}) compression"
            " (overrides .SUF in output NAME[.SUF])"
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
        version=f"%(prog)s {__version__}",
    )

    misc_opts = parser.add_argument_group("Shell completion options")
    misc_opts.add_argument(
        "--completion",
        help="Print bash completion for %(prog)s",
        action=CompletionPrintAction,
    )

    misc_opts.add_argument(
        "--bash-completion",
        help="Install bash completion for %(prog)s into"
        " ~/$XDG_DATA_DIR/bash-completion/completions/",
        action=BashCompletionInstall,
    )

    misc_opts.add_argument(
        "--zsh-completion",
        help="Install bash completion for %(prog)s into"
        " ~/$XDG_DATA_DIR/zsh-completions/",
        action=ZshCompletionInstall,
    )

    return parser.parse_args(args)
