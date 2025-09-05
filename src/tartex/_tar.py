# module _tar
"""
Helper class TarFiles
"""

from io import BytesIO
from pathlib import Path
from typing import Union
from .utils.tar_utils import strip_tarext, TAR_DEFAULT_COMP, TAR_EXT

class TarFiles:

    """Class that handles tarballing a list of objects (file Paths, BytesIO, etc.)"""

    # set of actual, accessible files to include
    _files: set

    # dict of objects to include whose contents are only available as BytesIO
    # key: name to use; val: object contents as BytesIO
    _streams: dict[str, BytesIO]

    # dict of strings to use for logging when adding `key` object to tarball
    # key: file or stream object name; val: logging string
    _comments: dict[str, str]

    def __init__(self, curr_dir: Path, main_input_file: Path, target: Path = Path('.')):
        """Init class for TarFiles"""
        self.main_file: Path = main_input_file
        self.working_dir: Path = self.main_file.parent
        target_path: Path = self.working_dir / target
        self.target: Path
        if target_path.is_dir():
            self.tar_ext: str = TAR_DEFAULT_COMP
            self.target = target_path / main_input_file.with_suffix(f".tar.{self.tar_ext}")
        else:
            if target_path.suffix not in TAR_EXT:
                self.tar_ext = TAR_DEFAULT_COMP
                self.target = strip_tarext(target_path).with_suffix(f'.tar.{self.tar_ext}')
            else:
                self.tar_ext = target_path.suffix
                self.target = target_path

    def recomp_mode(self, recomp: str):
        """Set re-compression mode for tarball

        :recomp: one of "bz2", "gz", or "xz" (str)
        :returns: None

        """
        self.tar_ext = recomp if recomp in TAR_EXT else "gz"
        self.target = self.target.with_suffix(self.tar_ext)

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
