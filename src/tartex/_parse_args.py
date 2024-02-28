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
from textwrap import fill, wrap

from tartex.__about__ import __appname__ as APPNAME, __version__
from tartex._completion import (
    COMPFILE,
    BashCompletion,
    FishCompletion,
    ZshCompletion,
)

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

    # TODO: This is a mess of print calls; see if it can be simplified
    def __call__(self, parser, namespace, values, option_string=None):
        fill_width = 80
        print(
            "Completion is currently supported for bash, fish, and zsh shells."
        )
        print(
            "Please consider contributing if you would like completion for"
            " any other shell.\n"
        )

        print(
            "----\n"  # do not join
            "Bash\n"  # do not join
            "----\n"  # do not join
            + fill(
                "The option `--bash-completion` will install bash completions"
                f" for {APPNAME} to the directory:",
                width=fill_width,
            )
            + f"\n${{XDG_DATA_HOME}}/{COMPFILE['bash'].parent!s}\n"
        )
        print(
            fill(
                "Bash automatically searches this dir for completions, so"
                f" completion for {APPNAME} should work immediately after"
                " starting a new terminal session."
                " If it does not, you may have to add the following lines"
                " to your .bashrc:",
                replace_whitespace=False,
                width=fill_width,
            )
        )
        bash_comp_path = BashCompletion().install_dir.joinpath(f"{APPNAME}")
        print(
            f"\n# Source {APPNAME} completion\n"
            f"source ~/{bash_comp_path.relative_to(Path.home())}",
        )
        print(
            "\n"  # do not join
            "---\n"  # do not join
            "Zsh\n"  # do not join
            "---\n"  # do not join
            + fill(
                "The option `--zsh-completion` will install a zsh completion"
                f" file for {APPNAME} to the directory:",
                width=fill_width,
            )
            + "\n"
            f"${{XDG_DATA_HOME}}/{COMPFILE['zsh'].parent!s}/\n"
            "\n"
            + fill(
                "It will also print what to add to your .zshrc file to enable"
                " these completions",
                width=fill_width,
            )
        )
        print(
            "\n"  # do not join
            "----\n"  # do not join
            "Fish\n"  # do not join
            "----\n"  # do not join
            + fill(
                "The option `--fish-completion` will install a fish completion"
                f" file for {APPNAME} to the directory:",
                width=fill_width,
            )
            + f"\n${{XDG_DATA_HOME}}/{COMPFILE['fish'].parent!s}/\n"
        )
        print(
            fill(
                "No further configuration should be needed. Simply start a"
                " new fish terminal et voila!"
            )
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

    def _split_lines(self, text, width):
        return wrap(text, width=52, break_on_hyphens=False)


def parse_args(args):
    """Set up argparse options and parse input args accordingly"""
    parser = argparse.ArgumentParser(
        description=(
            "Build a tarball including all source files needed to compile your"
            f" LaTeX project (version {__version__})."
        ),
        formatter_class=GnuStyleHelpFormatter,
        usage="%(prog)s [OPTIONS] FILENAME",
    )

    parser.add_argument(
        "fname",
        metavar="FILENAME",
        type=Path,
        help="input file name (with .tex or .fls suffix)",
    )

    parser.add_argument(
        "-V",
        "--version",
        help="print %(prog)s version and exit",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-a",
        "--add",
        metavar="PATTERNS",
        type=str,
        help=(
            "include additional files matching glob-style PATTERN;"
            " separate multiple PATTERNS using commas"
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
        help="print list of files to include and quit",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="NAME[.SUF]",
        type=Path,
        help="output tar file name; tar compression mode will be inferred from"
        " .SUF, if possible (default 'gz')",
    )

    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="print a summary at the end",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="increase verbosity (-v, -vv, etc.)",
        action="count",
        default=0,
    )

    parser.add_argument(
        "-x",
        "--excl",
        metavar="PATTERNS",
        type=str,
        help="exclude file names matching PATTERNS",
    )

    # Latexmk options
    latexmk_opts = parser.add_argument_group("Options for latexmk processing")
    latexmk_opts.add_argument(
        "--latexmk-tex",
        metavar="TEXMODE",
        choices=LATEXMK_TEX,
        default=None,
        help=(
            "force TeX processing mode used by latexmk;"
            f" TEXMODE must be one of: {', '.join(LATEXMK_TEX)}"
        ),
    )

    latexmk_opts.add_argument(
        "-F",
        "--force-recompile",
        action="store_true",
        help="force recompilation even if .fls exists",
    )

    # Tar recompress options
    tar_opts = parser.add_mutually_exclusive_group()

    def cmp_str(cmp, ext):
        return f"recompress with {cmp} (.{ext})" " (overrides .SUF in '-o')"

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

    misc_opts = parser.add_argument_group("Shell completion options")
    misc_opts.add_argument(
        "--completion",
        help="print shell completion guides for %(prog)s",
        action=CompletionPrintAction,
    )

    misc_opts.add_argument(
        "--bash-completions",
        help="install bash completions for %(prog)s",
        action=BashCompletionInstall,
    )

    misc_opts.add_argument(
        "--fish-completions",
        help="install fish completions for %(prog)s",
        action=FishCompletionInstall,
    )

    misc_opts.add_argument(
        "--zsh-completions",
        help="install zsh completions for %(prog)s",
        action=ZshCompletionInstall,
    )

    return parser.parse_args(args)
