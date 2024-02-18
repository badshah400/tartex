# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT

"""Tests for argument parsing"""

import pytest

from tartex.__about__ import __version__
from tartex.tartex import TarTeX, make_tar


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

    @pytest.mark.parametrize(
        ("tar_opt1", "tar_opt2"), [("-J", "-z"), ("-j", "-J"), ("-z", "-J")]
    )
    def test_taropts_conflict(self, capsys, tar_opt1, tar_opt2):
        """Test exit status when two conflicting tar options are passed"""
        with pytest.raises(SystemExit) as exc:
            TarTeX([tar_opt1, tar_opt2, "some_file.tex"])

        assert exc.value.code == 2
        output = capsys.readouterr().err
        assert "not allowed with" in output
