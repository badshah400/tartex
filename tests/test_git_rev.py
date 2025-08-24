# vim: set ai et ts=4 sw=4 tw=100:

import shutil
from subprocess import run, CalledProcessError
import pytest
from pathlib import Path

from tartex.tartex import TarTeX, TAR_DEFAULT_COMP

@pytest.fixture
def git_bin():
    """Returns the git executable available in PATH
    :returns: pathlib.Path

    """
    return shutil.which("git")


@pytest.fixture
def git_repo_clean(datadir, git_bin, capsys):
    """Set up a clean git repository

    """
    git_cmd_base = [git_bin, "-C", datadir]
    run([*git_cmd_base, "init", "-b", "main"])
    run([*git_cmd_base, "add", "."])
    run([*git_cmd_base, "commit", "-m", "Initial commit."])
    r = run([*git_cmd_base, "rev-parse", "HEAD"],
            capture_output=True,
            encoding="utf-8")
    return datadir, git_cmd_base, r.stdout.splitlines()[0].strip()


@pytest.fixture
def gitrev_tartex(datadir):
    return lambda rev: TarTeX(
            [
                (Path(datadir) / "git_rev").as_posix(),
                "-g",
                rev,
            ]
        )


class TestGitRev:

    """Test class for git-rev"""

    def test_default_tar_filename(self, git_repo_clean, datadir, git_bin, gitrev_tartex):
        git_repo, git, git_ref = git_repo_clean
        assert git_repo == datadir
        assert git_ref
        git_short_ref = git_ref[:7]
        # r1 should tarball working tree as it appeared at first commit
        r1 = gitrev_tartex(git_ref)
        assert f".{git_short_ref}" in Path(r1.tar_file_w_ext).suffixes

    def test_tarfile_change_tag(self, git_repo_clean, datadir, git_bin, gitrev_tartex):
        git_repo, git, git_ref = git_repo_clean
        git_short_ref = git_ref[:7]
        run(["sed", "-i", "s/test document/Test Document/", Path(datadir)/"git_rev.tex"])
        run([*git, "commit", "-a", "-m", "Second commit"])

        # r2 should tarball working tree as it appears at current HEAD
        r2 = gitrev_tartex("")
        assert f".{git_short_ref}" not in Path(r2.tar_file_w_ext).suffixes
