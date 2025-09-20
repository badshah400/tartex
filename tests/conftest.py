# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT

"""Common fixtures"""

import os
from pathlib import Path
import shutil
import time
import pytest

from tartex.tartex import TarTeX
import tartex.utils.xdgdir_utils as _tartex_xdg_utils


@pytest.fixture(autouse=True)
def setenv_term():
    """
    Ensure `rich` formatting does not get in the way of testing logs/stdout
    """
    os.environ["TERM"] = "dumb"


@pytest.fixture(autouse=True)
def mock_home(monkeypatch, tmp_path):
    """
    Mock `Path.home()` to return temporary path
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)


@pytest.fixture(autouse=True)
def mock_cache_dir(monkeypatch, tmp_path):
    """
    Mock XDG_CACHE_HOME with a 'cache' dir inside `tmp_path` to avoid polluting
    an actual user's XDG_CACHE_HOME dir.
    """
    monkeypatch.setattr(
        _tartex_xdg_utils, "XDG_CACHE_HOME", tmp_path / "cache",
    )


@pytest.fixture
def monkeypatch_mtime(monkeypatch):
    """
    Mock `os.path.getmtime(foo)` to return current time.

    Needed when we do not actually have a valid main tex/fls file to use for a
    test, but want to simply test `TarTeX` class variables anyway
    """
    return lambda _: monkeypatch.setattr(
        "os.path.getmtime", lambda _: time.time()
    )


@pytest.fixture
def monkeypatch_set_main_file(monkeypatch):
    """
    Mock `_set_main_file()` function to simply return the input path param
    without any checks.

    Needed when we do not actually have a valid main tex/fls file to use for a
    test, but want to simply test `TarTeX` class variables anyway
    """
    return lambda foo: monkeypatch.setattr(
        "tartex.tartex._set_main_file", lambda _: Path(foo)
    )


@pytest.fixture
def sample_texfile(monkeypatch_set_main_file, monkeypatch):
    """Pytest fixture: TarTeX with just a tex file for parameter"""

    # "some_file.tex" does not actually exist, but we use the dummy tartex
    # object to test class member variables anyway.
    #
    # For this dummy object to not cause early exit of TarTeX, we monkeypatch
    # `_set_main_file` to just return a path to the non-existent
    # "some_file.tex" instead of returning None. The latter would cause the
    # TarTeX object to hit sys.exit during __init__(), raising test errors.
    def mock_time(_):
        return time.time()

    monkeypatch.setattr("os.path.getmtime", mock_time)
    monkeypatch_set_main_file("some_file.tex")
    return TarTeX(["some_file.tex"])


# Data copying to tmpdir to allow using with pytest
# Note that relative paths to the data do not work as it is never certain which
# location pytest is run from
# Based on https://stackoverflow.com/a/29631801
@pytest.fixture
def datadir(tmpdir, request):
    """
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    """
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        shutil.copytree(test_dir, tmpdir, dirs_exist_ok=True)

    return tmpdir


@pytest.fixture
def join_linebreaks():
    """Joins lines with line breaks into one contiguous string

    :returns: Lambda that joins line at line breaks (str)

    """
    return lambda lbreaks: "".join(lbreaks.split("\n"))
