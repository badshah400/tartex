# module _tar
"""
Helper class TarFiles
"""

import os
from io import BytesIO
from pathlib import Path
from .utils.tar_utils import strip_tarext, TAR_DEFAULT_COMP, TAR_EXT


class TarFiles:
    """Class that handles tarballing a list of objects (file Paths, BytesIO, etc.)"""

    def __init__(
        self, curr_dir: Path, main_input_file: Path, target: Path = Path(".")
    ):
        """Init class for TarFiles"""

        # set of actual, accessible files to include
        self._files: set = set()

        # dict of objects to include whose contents are only available as BytesIO
        # key: name to use; val: object contents as BytesIO
        self._streams: dict[str, BytesIO]  = {}

        # dict of strings to use for logging when adding `key` object to tarball
        # key: file or stream object name; val: logging string
        self._comments: dict[str, str] = {}

        self._main_file: Path = main_input_file
        self._mtime = os.path.getmtime(self._main_file)

        self._work_dir: Path = self._main_file.parent
        target_path: Path = self._work_dir / target
        self._target: Path
        if target_path.is_dir():
            self._ext: str = TAR_DEFAULT_COMP
            self._target = target_path / main_input_file.with_suffix(
                f".tar.{self._ext}"
            )
        else:
            if target_path.suffix not in TAR_EXT:
                self._ext = TAR_DEFAULT_COMP
                self._target = strip_tarext(target_path).with_suffix(
                    f".tar.{self._ext}"
                )
            else:
                self._ext = target_path.suffix
                self._target = target_path

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
