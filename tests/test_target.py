# vim:set et sw=4 ts=4 tw=100:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT

"""Tests for different tar compression methods"""

from pathlib import Path
import pytest
import tempfile

from tartex.tartex import TarTeX
from tartex.utils.tar_utils import TAR_DEFAULT_COMP


@pytest.fixture
def target_tar(monkeypatch_set_main_file, monkeypatch_mtime):
    # See conftest.py for explanation of monkeypatching _set_main_file
    monkeypatch_set_main_file("some_file.tex")
    monkeypatch_mtime("some_file.tex")

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


class TestTarDir:
    """Class of tests checking user-entered dir as output path"""

    main_file = "some_file.tex"
    tartex_args = [main_file, "-s", "-v", "-o"]

    def test_output_dir(self, monkeypatch_set_main_file, monkeypatch_mtime):
        """Test tarball output when -o is existing dir"""
        monkeypatch_set_main_file(self.main_file)
        monkeypatch_mtime(self.main_file)

        with tempfile.TemporaryDirectory() as tmpdir:
            t = TarTeX([*self.tartex_args, f"{tmpdir!s}"])

            assert t.tar_file_w_ext == (
                (Path(tmpdir) / self.main_file).with_suffix(".tar.gz")
            )

    def test_output_dir_filename(
        self, monkeypatch_set_main_file, monkeypatch_mtime
    ):
        """
        Test tarball output when -o is file name in existing dir (default
        compression)
        """
        monkeypatch_set_main_file(self.main_file)
        monkeypatch_mtime(self.main_file)

        with tempfile.TemporaryDirectory() as tmpdir:
            t = TarTeX([*self.tartex_args, f"{tmpdir!s}/foo"])

            assert t.tar_file_w_ext == (
                (Path(tmpdir) / "foo").with_suffix(".tar.gz")
            )

    def test_output_dir_xz(self, monkeypatch_set_main_file, monkeypatch_mtime):
        """
        Test tarball output when -o is dir but '-J' is passed
        for xz compression
        """
        monkeypatch_set_main_file(self.main_file)
        monkeypatch_mtime(self.main_file)

        with tempfile.TemporaryDirectory() as tmpdir:
            t = TarTeX([*self.tartex_args, f"{tmpdir!s}", "-J"])

            assert t.tar_file_w_ext == (
                Path(tmpdir) / self.main_file
            ).with_suffix(".tar.xz")
