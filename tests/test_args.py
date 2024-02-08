# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT

"""Tests for argument parsing"""

import pytest

from tartex.__about__ import __version__
from tartex.tartex import TAR_DEFAULT_COMP, TarTeX, make_tar


class TestArgs:
    """Class to test different combinations of cmdline arguments"""

    def test_no_args(self):
        """Test system exit with missing positional arg"""
        with pytest.raises(SystemExit) as exc:
            make_tar()

        assert exc.value.code == 2

    def test_only_file(self):
        """Test success with one arg: file name"""
        t = TarTeX(["some_file.tex"])
        assert t.main_file.stem == "some_file"
        assert t.tar_file.name == "some_file.tar"

    def test_version(self, capsys):
        """Test version string against version from __about.py__"""
        # argparse will call SystemExit(0) for -h and -v, and print to stdout
        with pytest.raises(SystemExit) as exc:
            TarTeX(["--version"])

        output = capsys.readouterr().out
        assert f"{__version__}" in output
        assert exc.value.code == 0

    def test_taropts_conflict(self, capsys):
        """Test exit status when both --bzip2 and --gzip are passed"""
        with pytest.raises(SystemExit) as exc:
            TarTeX(["--bzip2", "--gzip"])

        assert exc.value.code == 2
        output = capsys.readouterr().err
        assert "not allowed with" in output


class TestTarExt:
    """
    Class of tests checking automatic tar compression detection based on user
    specified outout tarfile name
    """
    def test_default(self):
        """"Test default tarball extension"""
        t = TarTeX(["some_file.tex"])
        assert t.tar_ext == TAR_DEFAULT_COMP

    def test_output_bzip2(self):
        """Test user output file as .tar.bz2"""
        t = TarTeX(["-o", "dest.tar.bz2", "some_file.tex"])
        assert t.tar_ext == "bz2"
        t = TarTeX(["-o", "dest.tar.bz2", "-J", "some_file.tex"])
        assert t.tar_ext == "xz"
        assert t.tar_file.name == "dest.tar"

    def test_output_xz(self):
        """Test user output file as .tar.xz"""
        t = TarTeX(["-o", "dest.tar.xz", "some_file.tex"])
        assert t.tar_ext == "xz"
        t = TarTeX(["-o", "dest.tar.xz", "-j", "some_file.tex"])
        assert t.tar_ext == "bz2"
        assert t.tar_file.name == "dest.tar"
