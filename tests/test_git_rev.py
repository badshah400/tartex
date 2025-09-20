# vim: set ai et ts=4 sw=4 tw=100:

import hashlib
import shutil
import pytest
from pathlib import Path
from subprocess import run
import tarfile as tar

from tartex.tartex import TarTeX


@pytest.fixture
def git_bin():
    """Returns the git executable available in PATH
    :returns: str pointing to git binary or None if `git` in not found in Path

    """
    return shutil.which("git")


@pytest.fixture
def git_repo_clean(datadir, git_bin):
    """Set up a clean git repository"""
    git_cmd_base = [git_bin, "-C", datadir]
    run([*git_cmd_base, "init", "-b", "main"])
    run([*git_cmd_base, "add", "."])
    run([*git_cmd_base, "commit", "-m", "Initial commit."])
    r = run(
        [*git_cmd_base, "rev-parse", "HEAD"],
        capture_output=True,
        encoding="utf-8",
    )
    return datadir, git_cmd_base, r.stdout.splitlines()[0].strip()


@pytest.fixture
def gitrev_tartex(datadir):
    return lambda rev: TarTeX(
        [
            (Path(datadir) / "git_rev").as_posix(),
            "-vv",
            "-s",
            "-o",
            Path(datadir).as_posix(),
            "-g",
            rev,
        ]
    )


class TestGitRev:
    """Test class for git-rev"""

    def test_default_tar_filename(self, git_repo_clean, datadir, gitrev_tartex):
        git_repo, git, git_ref = git_repo_clean
        assert git_repo == datadir
        assert git_ref
        git_short_ref = git_ref[:7]
        # r1 should tarball working tree as it appeared at first commit
        r1 = gitrev_tartex(git_ref)
        assert (
            r1.main_file.stem + f"-git.{git_short_ref}.tar.{r1.tar_ext}"
        ) == r1.tar_file_w_ext.name

    def test_tarfile_change_tag(self, git_repo_clean, datadir, gitrev_tartex):
        git_repo, git, git_ref = git_repo_clean
        git_short_ref = git_ref[:7]
        run(
            [
                "sed",
                "-i",
                "s/test document/Test Document/",
                Path(datadir) / "git_rev.tex",
            ]
        )
        run([*git, "commit", "-a", "-m", "Second commit"])

        # r2 should tarball working tree as it appears at current HEAD
        r2 = gitrev_tartex("")
        assert f".{git_short_ref}" not in Path(r2.tar_file_w_ext).suffixes

    def test_final_git_branch_head(
        self, git_repo_clean, datadir, gitrev_tartex
    ):
        """Test whether we restore git tree pristinely at branch tip"""
        git_repo, git, git_ref = git_repo_clean
        run(
            [
                "sed",
                "-i",
                "s/test document/Test Document/",
                Path(datadir) / "git_rev.tex",
            ]
        )
        run([*git, "commit", "-a", "-m", "Second commit"])
        # Now we are at "HEAD", pointing to "main" branch tip...
        gitrev_tartex(git_ref)
        git_status = run(
            [*git, "status"], capture_output=True, check=True, encoding="utf-8"
        )
        # ...first line should be "On branch main"
        assert "On branch" in git_status.stdout.splitlines()[0]

    def test_final_git_detach_head(
        self, git_repo_clean, datadir, gitrev_tartex
    ):
        """Test whether we restore git tree back to detached head if that is
        the initial status of the tree
        """
        git_repo, git, git_ref = git_repo_clean
        run(
            [
                "sed",
                "-i",
                "s/test document/Test Document/",
                Path(datadir) / "git_rev.tex",
            ]
        )
        run([*git, "commit", "-a", "-m", "Second commit"])
        git_ref_2 = run(
            [*git, "rev-parse", "HEAD"],
            capture_output=True,
            encoding="utf-8",
        ).stdout.strip()
        run([*git, "checkout", "--detach", git_ref])
        # Now we are at detached "HEAD", pointing to initial commit...
        gitrev_tartex(git_ref_2)
        git_status = run(
            [*git, "status"], capture_output=True, check=True, encoding="utf-8"
        )
        # ...first line should be "HEAD detached at"
        assert "HEAD detached at" in git_status.stdout.splitlines()[0]

    def test_tar_contents(self, git_repo_clean, datadir, gitrev_tartex, capsys):
        """validate `git_rev.tex` in tarball against original file"""

        git_repo, git, git_ref = git_repo_clean
        git_short_ref = git_ref[:7]
        with open(Path(datadir) / "git_rev.tex", "rb") as f:
            r1_tex_data = f.read()
            r1_texfile_sha = hashlib.sha1(r1_tex_data)

        run(
            [
                "sed",
                "-i",
                "s/test document/Test Document/",
                Path(datadir) / "git_rev.tex",
            ]
        )
        run([*git, "commit", "-a", "-m", "Second commit"])

        t = gitrev_tartex(git_short_ref)
        t.tar_files()

        with tar.open(t.tar_file_w_ext, "r") as tf:
            tex_file = tf.extractfile(t.main_file.name)
            if tex_file:
                tex_data = tex_file.read()
                assert tex_data.decode("utf-8") == r1_tex_data.decode("utf-8")
                tex_data_sha1 = hashlib.sha1(tex_data)
                assert tex_data_sha1.hexdigest() == r1_texfile_sha.hexdigest()


    def test_git_default_head(self, git_repo_clean, datadir, caplog):
        """
        Check that default git ref used is HEAD
        """
        git_repo, git, git_ref = git_repo_clean
        tar_git = TarTeX(
            [
                (Path(datadir) / "git_rev").as_posix(),
                "-vv",
                "-s",
                "-o",
                Path(datadir).as_posix(),
                "-g",
            ]
        )
        assert f"git.{git_ref[:7]}" == tar_git.GR.id()
