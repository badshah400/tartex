# vim:set et sw=4 ts=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""Tests for tarball generation from basic latex files"""

from pathlib import Path

import pytest

from tartex.tartex import TarTeX, chdir


@pytest.fixture
def default_target(datadir):
    return Path(datadir) / "test"


@pytest.fixture
def default_tartex_obj(datadir, default_target):
    return lambda fname: TarTeX(
        [
            (Path(datadir) / fname).as_posix(),
            "-v",
            "-s",
            "-o",
            default_target.as_posix(),
        ]
    )


class TestLaTeXmkFail:
    """Tests checking error reporting and clean up when latexmk fails"""

    def test_cleanup(self, default_target, default_tartex_obj):
        """Should clean up tarball when latexmk fails"""
        with chdir(default_target.parent):
            t = default_tartex_obj("error_latex.tex")
            with pytest.raises(SystemExit) as exc:
                t.tar_files()

            assert exc.value.code != 1  # exit code == 4 for latexmk errors
            assert not t.tar_file_w_ext.exists()

    def test_err_msg(self, default_target, datadir, caplog):
        """Should print an error msg when latexmk fails"""
        with chdir(datadir):
            t = TarTeX(
                [
                    "error_latex.tex",
                    "-vv",
                    "-s",
                    "-o",
                    "error_latex.tar.xz",
                ]
            )
            with pytest.raises(SystemExit) as exc:
                t.tar_files()

            logs = " ".join(caplog.messages)
            assert "latexmk failed to compile project" in logs
            assert "l.7 [Undefined control sequence]" in logs
            assert "See tartex_compile_error.log" in logs
            assert exc.value.code == 4
