# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT

"""Tests for argument parsing"""

import argparse
import pytest
from tartex.tartex import TarTeX, make_tar


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
