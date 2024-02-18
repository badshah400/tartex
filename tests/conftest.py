# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT

"""Common fixtures"""

import os
import shutil

import pytest

from tartex.tartex import TarTeX


@pytest.fixture
def sample_texfile():
    """Pytest fixture: TarTeX with just a tex file for parameter"""
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
