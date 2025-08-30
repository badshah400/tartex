# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT

"""Tests for different tar compression methods"""

from pathlib import Path
import pytest

from tartex.tartex import TarTeX
from tartex.utils.tar_utils import TAR_DEFAULT_COMP


@pytest.fixture
def target_tar(monkeypatch_set_main_file):
    # See conftest.py for explanation of monkeypatching _set_main_file
    monkeypatch_set_main_file("some_file.tex")
    def _target(tar_ext, cmp_opt=""):
        ttx_opts = ["-v", "-s", "-o", f"dest.tar.{tar_ext}", "some_file.tex"]
        if cmp_opt:
            ttx_opts.append(cmp_opt)
        return TarTeX(ttx_opts)

    return _target


class TestTarExt:
    """
    Class of tests checking automatic tar compression detection based on user
    specified outout tarfile name
    """

    def test_default_compress(self, sample_texfile):
        """Test default tarball extension"""
        assert sample_texfile.tar_ext == TAR_DEFAULT_COMP

    def test_output_file_compress(self, target_tar):
        """Test user output file for different tar.foo extensions"""
        # bz2
        assert target_tar("bz2").tar_ext == "bz2"
        # tar.bz2 overridden by "-J"
        assert target_tar("bz2", "-J").tar_ext != "bz2"
        # xz
        assert target_tar("xz").tar_ext == "xz"
        assert (
            target_tar("xz").tar_file_w_ext.with_suffix("").name == "dest.tar"
        )
