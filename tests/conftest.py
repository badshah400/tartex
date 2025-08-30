# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT

"""Common fixtures"""

import os
from pathlib import Path
import shutil

import pytest

from tartex.tartex import _set_main_file, TarTeX

@pytest.fixture
def monkeypatch_set_main_file(monkeypatch):
    return lambda foo: monkeypatch.setattr("tartex.tartex._set_main_file", lambda _: Path(foo))

@pytest.fixture
def sample_texfile(monkeypatch_set_main_file):
    """Pytest fixture: TarTeX with just a tex file for parameter"""

    # "some_file.tex" does not actually exist, but we use the dummy tartex
    # object to test class member variables anyway.
    #
    # For this dummy object to not cause early exit of TarTeX, we monkeypatch
    # `_set_main_file` to just return a path to the non-existent
    # "some_file.tex" instead of returning None. The latter would cause the
    # TarTeX object to hit sys.exit during __init__(), raising test errors.
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
