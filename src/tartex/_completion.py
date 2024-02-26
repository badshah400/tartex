# vim:set et sw=4 ts=4:
"""
Module to help users with completion syntax for tartex
"""

from pathlib import Path
from shutil import copy2
import os
from tartex.__about__ import __appname__ as APPNAME

COMPFILE = {
    "bash": Path(f"bash-completion/completions/{APPNAME}"),
    "fish": Path(f"fish/vendor_completions.d/{APPNAME}.fish"),
    "zsh": Path(f"zsh-completions/_{APPNAME}"),
}


class Completion:

    """Methods for helping users print or install shell completion"""

    def __init__(self, shell, filename):
        """Initialise"""
        self.shell = shell
        self.completion_file = Path(__file__).parent.joinpath("data", filename)
        self.data = self.completion_file.read_text(encoding="utf-8")

        install_root = Path(
            os.getenv("XDG_DATA_HOME") or Path.home().joinpath(".local", "share")
        )
        self.install_dir = install_root.joinpath(COMPFILE[self.shell]).parent
        self.install_filename = COMPFILE[self.shell].name

    def print(self):
        """Print completion to stdout"""
        print(self.data, end="")

    def install(self, install_dir=None):
        """Install completion to path"""
        path = Path(install_dir or self.install_dir)
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        inst_path = Path(
            copy2(self.completion_file, path.joinpath(self.install_filename))
        )
        print(
            f"Completion file for {self.shell} shell installed to"
            f" {inst_path.parent}"
        )


class BashCompletion(Completion):

    """Completion for bash"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(
            self, shell="bash", filename="tartex-completion.bash"
        )


class ZshCompletion(Completion):

    """Completion for zsh shell"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(self, shell="zsh", filename="tartex-completion.zsh")


class FishCompletion(Completion):

    """Completion for fish shell"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(
            self, shell="fish", filename="tartex-completion.fish"
        )
