# module _tar
"""
Helper class TarFiles
"""

import logging as log
import os
import sys
from io import BytesIO
from pathlib import Path
from .utils.tar_utils import TAR_EXT
import tarfile as tar

class Tarballer:
    """Class that handles tarballing a list of objects (file Paths, BytesIO, etc.)"""

    def __init__(
        self, curr_dir: Path, main_input_file: Path, target: Path = Path(".")
    ):
        """Init class for TarFiles"""

        # Count of objects included in tarball
        self._num_objects: int = 0

        # set of actual, accessible files to include
        self._files: set[Path] = set()

        # dict of objects to include whose contents are only available as BytesIO
        # key: name to use; val: object contents as BytesIO
        self._streams: dict[str, BytesIO]  = {}

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

    def num_objects(self) -> int:
        """Returns the total number of files and bytes objects added to tarball
        :returns: int

        """
        return self._num_objects

    def recomp_mode(self, recomp: str):
        """Set re-compression mode for tarball

        :recomp: one of "bz2", "gz", or "xz" (str)
        :returns: None

        """
        self._ext = recomp if recomp in TAR_EXT else "gz"
        self._target = self._target.with_suffix(self._ext)

    def set_mtime(self, mtime: int):
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
            tar_obj: tar.TarFile, file_name: Path,
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
            with tar.open(self._target, mode=f"w:{self._ext}") as tar_obj:
                for dep in self._files:
                    try:
                        _tar_add_file(tar_obj, dep)
                    except FileNotFoundError:
                        log.warning(
                            "Skipping INPUT file '%s', not found amongst sources; try"
                            " forcing a LaTeX recompile ('-F').",
                            dep,
                        )
                        continue
                    self._num_objects += 1
                for key, val in self._streams.items():
                    _tar_add_bytesio(tar_obj, key, val)
                    self._num_objects += 1
        except PermissionError as e:
            log.critical(e)
            sys.exit(1)
        except Exception as e:
            raise e
