# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT

"""Tests for argument parsing"""

import pytest

from tartex.__about__ import __version__
from tartex.tartex import TAR_DEFAULT_COMP, TarTeX, make_tar

@pytest.fixture
def sample_texfile():
    """Pytest fixture: TarTeX with just a tex file for parameter"""
    t = TarTeX(["some_file.tex"])
    return t


class TestArgs:
    """Class to test different combinations of cmdline arguments"""

    def test_no_args(self):
        """Test system exit with missing positional arg"""
        with pytest.raises(SystemExit) as exc:
            make_tar()

        assert exc.value.code == 2

    def test_only_file(self, sample_texfile):
        """Test success with one arg: file name"""
        assert sample_texfile.main_file.stem == "some_file"
        assert sample_texfile.tar_file.name == "some_file.tar"

    def test_version(self, capsys):
        """Test version string against version from __about.py__"""
        # argparse will call SystemExit(0) for -h and -v, and print to stdout
        with pytest.raises(SystemExit) as exc:
            TarTeX(["--version"])

        output = capsys.readouterr().out
        assert f"{__version__}" in output
        assert exc.value.code == 0

    @pytest.mark.parametrize("tar_opt1, tar_opt2", [("-J", "-z"),
                                                    ("-j", "-J"),
                                                    ("-z", "-J")])
    def test_taropts_conflict(self, capsys, tar_opt1, tar_opt2):
        """Test exit status when two conflicting tar options are passed"""
        with pytest.raises(SystemExit) as exc:
            TarTeX([tar_opt1, tar_opt2, "some_file.tex"])

        assert exc.value.code == 2
        output = capsys.readouterr().err
        assert "not allowed with" in output


@pytest.fixture
def target_tar():
    def _target(tar_ext, cmp_opt = ""):
        ttx_opts = ["-o", f"dest.tar.{tar_ext}", "some_file.tex"]
        if cmp_opt:
            ttx_opts.append(cmp_opt)
        return TarTeX(ttx_opts)
    return _target

class TestTarExt:
    """
    Class of tests checking automatic tar compression detection based on user
    specified outout tarfile name
    """
    def test_default(self, sample_texfile):
        """"Test default tarball extension"""
        assert sample_texfile.tar_ext == TAR_DEFAULT_COMP

    def test_output_compress(self, target_tar):
        """Test user output file for different tar.foo extensions"""
        # bz2
        assert target_tar("bz2").tar_ext == "bz2"
        # tar.bz2 overridden by "-J"
        assert not target_tar("bz2", "-J").tar_ext == "bz2"
        # xz
        assert target_tar("xz").tar_ext == "xz"
        assert target_tar("xz").tar_file.name == "dest.tar"
