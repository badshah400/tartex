# vim:set et sw=4 ts=4:
"""
Module to help users with completion syntax for tartex
"""

from pathlib import Path
from shutil import copy2
import os

APPNAME = "tartex"
COMPDIR = {"bash": "bash-completion/completions"}


class Completion:

    """Methods for helping users print or install shell completion"""

    def __init__(self, shell, filename):
        """Initialise"""
        self.shell = shell
        self.completion_file = Path(__file__).parent.joinpath("data", filename)
        self.data = self.completion_file.read_text(encoding="utf-8")

        install_root = Path(
            os.getenv("XDG_DATA_DIR") or Path.home().joinpath(".local", "share")
        )
        self.install_dir = install_root.joinpath(COMPDIR[self.shell])

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
        inst_path = Path(copy2(self.completion_file, path / APPNAME))
        print(
            f"Completion file for {self.shell} shell installed to {inst_path.parent}"
        )


class BashCompletion(Completion):

    """Completion for bash"""

    def __init__(self):
        """Initialise"""
        Completion.__init__(
            self, shell="bash", filename="tartex-completion.bash"
        )
