# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""
Tests for when source dir has .fls file
"""

import tarfile as tar

import pytest

from tartex.tartex import TAR_DEFAULT_COMP, TarTeX


@pytest.fixture
def flsfile():
    """Default fls file name"""
    return "main.fls"


@pytest.fixture
def tartex_obj(datadir, flsfile):
    """Default tartex object with flsfile as input"""
    return TarTeX(
        [str(datadir / flsfile), "-o", str(datadir), "-bs"],
    )


def test_fls_main_arg(tartex_obj, flsfile):
    """User passes a .fls filename as input"""
    t = tartex_obj
    assert t.tar_file.name == flsfile.replace(".fls", ".tar")


def test_fls_missing_bbl(tartex_obj, flsfile):
    """
    Verify that missing .bbl file is omitted from tarball and the cal to
    tar_files() does not cause an exception
    """
    tartex_obj.tar_files()

    with tar.open(f"{tartex_obj.tar_file!s}.{TAR_DEFAULT_COMP}") as f:
        assert flsfile.replace(".fls", ".bbl") not in f.getnames()


def test_fls_recompile(datadir, flsfile):
    """Forcing a LaTeX recompile ensures .bbl is included"""
    t = TarTeX([str(datadir / flsfile), "-o", str(datadir), "-b", "-F"])
    t.tar_files()

    with tar.open(f"{t.tar_file!s}.{TAR_DEFAULT_COMP}") as f:
        assert flsfile.replace(".fls", ".bbl") in f.getnames()
