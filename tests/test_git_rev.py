# vim: set ai et ts=4 sw=4 tw=100:

import shutil
from subprocess import run, CalledProcessError
import pytest
from pathlib import Path

from tartex.tartex import TarTeX, TAR_DEFAULT_COMP

@pytest.fixture
def git_bin() -> Path:
    """Returns the git executable available in PATH
    :returns: pathlib.Path

    """
    return shutil.which("git")


@pytest.fixture
def git_repo_clean(datadir, git_bin, capsys):
    """Set up a clean git repository

    """
    git_cmd_base = [git_bin, "-C", datadir]
    git_cmd = run([*git_cmd_base, "init", "-b", "main"])
    run([*git_cmd_base, "add", "."])
    run([*git_cmd_base, "commit", "-m", "Initial commit."])
    run([*git_cmd_base, "ls-tree", "HEAD"], capture_output=True)
    r = run([*git_cmd_base, "rev-parse", "HEAD"],
            capture_output=True,
            encoding="utf-8")
    return datadir, git_cmd_base, r.stdout.splitlines()[0].strip()


class TestGitRev:

    """Test for git-rev"""

    def test_git_init(self, git_repo_clean, datadir, git_bin):
        git_repo, git, git_ref = git_repo_clean
        assert git_repo
        assert git_ref
        git_short_ref = git_ref[:7]
        run(["sed", "-i", "s/test document/Test Document/", Path(datadir)/"git_rev.tex"])
        run([*git, "commit", "-a", "-m", "Second commit"])
        r = TarTeX(
            [
                (Path(datadir) / "git_rev").as_posix(),
                "-v",
                "-s",
                "-g",
                git_ref,
            ]
        )
        assert f".{git_short_ref}" in Path(r.tar_file_w_ext).suffixes
