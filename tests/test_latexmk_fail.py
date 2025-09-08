# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""Tests for tarball generation from basic latex files"""

from pathlib import Path

import pytest

from tartex.tartex import TarTeX


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

    def test_cleanup(self, default_target, default_tartex_obj, capsys):
        """Should clean up tarball when latexmk fails"""
        t = default_tartex_obj("error_latex.tex")
        with pytest.raises(SystemExit) as exc:
            t.tar_files()

        assert exc.value.code == 1
        assert not t.tar_file_w_ext.exists()

    def test_err_msg(self, default_target, datadir, capsys, join_linebreaks):
        """Should print an error msg when latexmk fails"""
        t = TarTeX(
            [
                (Path(datadir) / "error_latex.tex").as_posix(),
                "-vv",
                "-s",
                "-o",
                default_target.with_suffix(".xz").as_posix(),
            ]
        )
        with pytest.raises(SystemExit) as exc:
            t.tar_files()
            assert (
                "latexmk failed with the following output"
                in join_linebreaks(capsys.readouterr().err)
            )
            assert "command used was:" in capsys.readouterr().err
            assert "Cleaning up empty tarball" in join_linebreaks(
                capsys.readouterr().err
            )

        assert exc.value.code == 1
