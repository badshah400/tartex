# module _tar
"""
Helper class TarFiles
"""

import logging as log
import math
import os
import sys
from io import BytesIO
from pathlib import Path
from rich import print as richprint
from .utils.tar_utils import TAR_EXT
from .utils.msg_utils import summary_msg
import tarfile as tar


class Tarballer:
    """Class that handles tarballing a list of objects (file Paths, BytesIO, etc.)"""

    def __init__(
        self, curr_dir: Path, main_input_file: Path, target: Path = Path(".")
    ):
        """Init class for TarFiles"""

        # set of actual, accessible files to include
        self._files: set[Path] = set()

        # dict of objects to include whose contents are only available as BytesIO
        # key: name to use; val: object contents as BytesIO
        self._streams: dict[str, BytesIO] = {}

        # dict of strings to use for logging when adding `key` object to tarball
        # key: file or stream object name; val: logging string
        self._comments: dict[str, str] = {}

        self._main_file: Path = main_input_file
        self._mtime = os.path.getmtime(self._main_file)

        self._work_dir: Path = curr_dir
        target_path: Path = self._work_dir / target
        self._target: Path
        self._ext = target_path.suffix.lstrip(".")
        self._target = target_path.with_suffix(f".{self._ext}")

    @property
    def num_objects(self) -> int:
        """Returns the total number of files and bytes objects added to tarball
        :returns: int

        """
        return len(self._files) + len(self._streams)

    def recomp_mode(self, recomp: str):
        """Set re-compression mode for tarball

        :recomp: one of "bz2", "gz", or "xz" (str)
        :returns: None

        """
        self._ext = recomp if recomp in TAR_EXT else "gz"
        self._target = self._target.with_suffix(self._ext)

    def set_mtime(self, mtime: float):
        """Set mtime for bytesio objects, for which mtime is not available otherwise"""
        self._mtime = mtime

    def app_files(self, *args: Path, comm: str = ""):
        """Update set of files to add to tarball with args

        :*args: files to append to `self._files` as args
        :returns: None

        """
        self._files.update(args)
        for f in args:
            if comm:
                self._comments[f.as_posix()] = comm

    def drop_files(self, *args: Path):
        """Drop files and associated comments, if any"""
        for f in args:
            self._files.discard(f)
            _ = self._comments.pop(f.as_posix(), None)

    def files(self) -> set[Path]:
        """Return copy of self._files as a set of Path(s)
        :returns: set of Paths

        """
        return self._files.copy()

    def streams(self) -> set[str]:
        """Return copy of self._streams.keys() as a set of strings
        :returns: set of str

        """
        return set(self._streams.keys())

    def objects(self) -> set[Path]:
        """Return all files and streams to be added to tarball"""
        return self.files().union([Path(f) for f in self.streams()])

    def app_stream(self, name: str, content: BytesIO, comm: str = ""):
        """Append a single BytesIO content to list of streams

        :name: file name to use for stream (str)
        :content: stream content corresponding to `name` (BytesIO)
        :returns: None

        """
        self._streams[name] = content
        if comm:
            self._comments[name] = comm

    def do_tar(self):
        def _tar_add_file(
            tar_obj: tar.TarFile,
            file_name: Path,
        ):  # helper func to add file <file_name> to <tar_obj>
            tinfo = tar_obj.gettarinfo(file_name)
            tinfo.uid = tinfo.gid = 0
            tinfo.uname = tinfo.gname = ""
            tar_obj.addfile(tinfo, open(file_name, "rb"))
            log.info("Add file: %s", file_name)

        def _tar_add_bytesio(tar_obj: tar.TarFile, file_name: str, obj):
            # helper func to add `obj` as BytesIO with filename <file_name> to <tar_obj>
            tinfo = tar_obj.tarinfo(file_name)
            tinfo.size = len(obj)
            tinfo.mtime = self._mtime
            tinfo.uid = tinfo.gid = 0
            tinfo.uname = tinfo.gname = ""
            tar_obj.addfile(tinfo, BytesIO(obj))
            log.info("Add contents as BytesIO: %s", file_name)

        # At this point, output tar name conflicts, if any, has been
        # resolved one way or another, and we should simply over-write
        # tarball if it exists. So, it is safe to use 'w:'
        try:
            lof = self._files.copy()
            with tar.open(self._target, mode=f"w:{self._ext}") as tar_obj:
                for dep in lof:
                    try:
                        _tar_add_file(tar_obj, dep)
                    except FileNotFoundError:
                        log.warning(
                            "Skip missing INPUT file '%s'; try"
                            " forcing a LaTeX recompile ('-F').",
                            dep,
                        )
                        self._files.discard(dep)
                        continue
                for key, val in self._streams.items():
                    _tar_add_bytesio(tar_obj, key, val)
        except PermissionError as e:
            log.critical(e)
            raise e
        except Exception as e:
            raise e

    def print_list(self, _summ: bool = False):
        """helper function to print list of files in a pretty format"""
        total = len(self._files) + len(self._streams)
        idx_width = int(math.log10(total)) + 1  # num of chars for serial nums
        files_cnt = 0
        for f in sorted(self._files):
            if f.exists():
                richprint(f"{files_cnt + 1:{idx_width}}.", end=" ")
                print(str(f))
                files_cnt += 1
            else:
                log.warning("Missing file skipped: %s", f)
                total -= 1
        for r in sorted(self._streams.keys()):
            richprint(f"{'*':>{idx_width + 1}}", end=" ")
            print(f"{r}")
        if _summ:
            summary_msg(total)
