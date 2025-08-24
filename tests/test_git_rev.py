# vim: set ai et ts=4 sw=4 tw=100:

import shutil
from subprocess import run, CalledProcessError
import pytest
from pathlib import Path
import tarfile as tar

from tartex.tartex import TarTeX, TAR_DEFAULT_COMP


@pytest.fixture
def git_bin():
    """Returns the git executable available in PATH
    :returns: pathlib.Path

    """
    return shutil.which("git")


@pytest.fixture
def git_repo_clean(datadir, git_bin, capsys):
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
        assert f".{git_short_ref}" in Path(r1.tar_file_w_ext).suffixes

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
            [*git, "rev-parse", "HEAD"], capture_output=True, encoding="utf-8",
        ).stdout.strip()
        run([*git, "checkout", "--detach", git_ref])
        # Now we are at detached "HEAD", pointing to initial commit...
        gitrev_tartex(git_ref_2)
        git_status = run(
            [*git, "status"], capture_output=True, check=True, encoding="utf-8"
        )
        # ...first line should be "HEAD detached at"
        assert (
            "HEAD detached at" in git_status.stdout.splitlines()[0]
        )

    def test_tar_contents(self, git_repo_clean, datadir, gitrev_tartex, capsys):
        """validate `git_rev.tex` in tarball against `git cat-file`"""

        git_repo, git, git_ref = git_repo_clean
        git_short_ref = git_ref[:7]

        # We only have one file, so `git ls-tree --long` should be just a single line
        r1_ls_tree = run(
            [*git, "ls-tree", "--long", git_ref],
            capture_output=True,
            check=True,
        )
        r1_texfile_sha, r1_texfile_size = r1_ls_tree.stdout.splitlines()[
            0
        ].split()[2:4]

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
                tex_data = tex_file.read().decode("utf-8")
                r1_tex_data = run(
                    [
                        *git,
                        "cat-file",
                        "-p",
                        r1_texfile_sha,
                    ],
                    capture_output=True,
                    check=True,
                    encoding="utf-8",
                ).stdout
                assert tex_data == r1_tex_data
