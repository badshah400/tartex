# vim:set et sw=4 ts=4:
"""
Module to help users with completion syntax for tartex
"""

import contextlib
import os
from pathlib import Path
from shutil import copy2

from rich import print as richprint

from tartex.__about__ import __appname__ as APPNAME  # noqa

COMPFILE = {
    "bash": Path(f"bash-completion/completions/{APPNAME}"),
    "fish": Path(f"fish/vendor_completions.d/{APPNAME}.fish"),
    "zsh": Path(f"zsh-completions/_{APPNAME}"),
}


class Completion:

    """Methods for helping users print or install shell completion"""

    def __init__(self, shell_name, filename):
        """Initialise"""
        self.shell = shell_name
        self.completion_file = Path(__file__).parent.joinpath("data", filename)
        self.data = self.completion_file.read_text(encoding="utf-8")

        install_root = Path(
            os.getenv("XDG_DATA_HOME")
            or Path.home().joinpath(".local", "share")
        )
        self.install_dir = install_root.joinpath(COMPFILE[self.shell]).parent
        self.install_filename = COMPFILE[self.shell].name

    def install(self, install_dir=None):
        """Install completion to path"""
        path = Path(install_dir or self.install_dir)
        with contextlib.suppress(FileExistsError):
            os.makedirs(path)
        inst_path = Path(
            copy2(self.completion_file, path.joinpath(self.install_filename))
        )
        richprint(
            f"✓ Completion file for [bold]{self.shell}[/] shell installed to"
            f" [link={inst_path.parent.as_uri()}]{inst_path.parent}[/]"
        )


class BashCompletion(Completion):

    """Completion for bash"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(
            self, shell_name="bash", filename="tartex-completion.bash"
        )


class ZshCompletion(Completion):

    """Completion for zsh shell"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(
            self, shell_name="zsh", filename="tartex-completion.zsh"
        )


class FishCompletion(Completion):

    """Completion for fish shell"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(
            self, shell_name="fish", filename="tartex-completion.fish"
        )
