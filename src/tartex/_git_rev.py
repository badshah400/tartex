# vim: set et ai ts=4 sw=4 tw=100:

import shutil
import subprocess
import logging as log
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def git_checkout(git_bin: str, repo: str, rev: str):
    """
    A context manager for git checkout that checks out `rev` and restores previous working tree
    afterwards
    """

    head_full_ref = _get_ref(git_bin, repo, "HEAD")
    head_short_ref = head_full_ref[:7]
    try:
        rev_full_ref = _get_ref(git_bin, repo, rev)
        rev_short_ref = rev_full_ref[:7]
    except subprocess.CalledProcessError as err:  # typically for invalid rev
        log.critical("Failed to checkout revision %s; invalid git revision?", rev)
        log.critical("Git: %s", err.stderr.strip())
        raise err

    if head_full_ref != rev_full_ref:
        try:
            # Note: git prints checkout msgs to stderr, not stdout
            rev_proc = subprocess.run(
                [git_bin, "-C", repo, "checkout", "--detach", rev],
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
            log.info("Checking out git revision %s in detached mode", rev)
            for line in rev_proc.stderr.splitlines():
                log.debug("Git: %s", line)

            yield rev_short_ref
        finally:
            head_proc = subprocess.run(
                [git_bin, "-C", repo, "checkout", "-f", head_full_ref],
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
            log.info("Restoring git working tree to rev %s", head_short_ref)
            for line in head_proc.stderr.splitlines():
                log.debug("Git: %s", line)
    else:
        log.debug("Using current git working tree at %s", head_short_ref)
        yield rev_short_ref


def _get_ref(git_bin, repo, rev):
    """Returns the full ref for a given git revision `rev` in a git `repo`"""

    return subprocess.run(
        [git_bin, "-C", repo, "rev-parse", rev],
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()[0]


class GitRev:
    """Class to set up and obtain file list from a git repo"""

    def __init__(self, repo: str, rev: str = "HEAD") -> None:
        """Initialise GitRev class

        :repo: dir containing a git repo (str)
        :rev: a valid git revision (str), default: "HEAD"

        """
        self.repo: str = str(repo)
        self.rev: str = rev
        self.git_bin = shutil.which("git")
        if not self.git_bin:
            raise RuntimeError("Unable to find git executable in PATH")

    def id(self) -> str:
        """Return either tag name, if commit corresponds to a valid tag, or commit short-id
        otherwise

        :returns: str

        """
        # The first line of the commit is something like the following:
        # ```
        # commit SHORT_ID
        # ```
        self.git_commit_id = self._git_cmd(
            [
                "show",
                "--abbrev-commit",
                "--no-patch",
                "--no-color",
                self.rev,
            ]
        )[0]

        self.tag_id: str | None
        try:
            self.tag_id = self._git_cmd(
                [
                    "describe",
                    "--tags",
                    "--exact-match",
                    self.rev,
                ]
            )[0]
        except Exception:
            self.tag_id = None

        return self.tag_id or f"git.{self.git_commit_id.split()[1]}"

    def ls_tree_files(self):
        """Get list of files from ls-tree
        :returns: dict[Path]

        """
        _files = self._git_cmd(
            [
                "ls-tree",
                "-r",
                "--name-only",
                self.rev,
            ]
        )

        self.ls_tree_paths = [Path(f) for f in _files]

        return self.ls_tree_paths

    def _git_cmd(self, cmd: list[str]) -> list[str]:
        """Run specified cmd and return captured output

        :cmd: git command to run (list[str])
        :returns: list of lines from output (list[str])
        :raises: OSError, subprocess.CalledProcessError

        """

        git_comm = [f"{self.git_bin!s}", "-C", f"{self.repo!s}"] + cmd
        try:
            out = subprocess.run(
                git_comm, capture_output=True, encoding="utf-8", check=True
            )
        except OSError as err:
            log.critical("%s", err.strerror)
            raise err
        except subprocess.CalledProcessError as err:
            log.critical(
                "Error: %s failed with the following output:\n%s\n%s",
                err.cmd[0],
                err.stdout,
                "===================================================",
            )
            raise err
        return out.stdout.splitlines()
