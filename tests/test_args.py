# vim:set et sw=4 ts=4:
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

        # Weird: `hatch test -v` gets `exc.value.code = 1`, but `hatch test`
        # (without `-v`) gets `2`.  Actual value must be 1 --- there is no
        # `sys.exit(2)` in code, but help `hatch test` out.
        assert exc.value.code >= 1

    def test_only_file(self, sample_texfile):
        """Test success with one arg: file name"""
        assert sample_texfile.main_file.stem == "some_file"
        assert (
            sample_texfile.tar_file_w_ext.name
            == f"some_file.tar.{sample_texfile.tar_ext}"
        )

    def test_no_main_file(self, caplog):
        """Test error msg when specified main tex file is not found"""
        with pytest.raises(SystemExit) as exc:
            TarTeX(["foo", "-v"])

        assert 1 == exc.value.code
        assert "Main input file not found: foo.(tex|fls)" in caplog.text

    def test_version(self, capsys, join_linebreaks):
        """Test version string against version from __about.py__"""
        # argparse will call SystemExit(0) for -h and -v, and print to stdout
        with pytest.raises(SystemExit) as exc:
            TarTeX(["--version"])

        output = join_linebreaks(capsys.readouterr().out)
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
