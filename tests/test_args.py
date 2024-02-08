# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT

"""Tests for argument parsing"""

import pytest
from tartex.tartex import TarTeX, make_tar
from tartex.__about__ import __version__


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
