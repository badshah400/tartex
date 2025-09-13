# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""Tests for LaTeX project consisting of multiple dirs"""

import fileinput
import os
import tarfile as tar
from pathlib import Path

import pytest

from tartex.tartex import TarTeX


@pytest.fixture
def multidir_target(datadir):
    return Path(datadir) / "multi"


@pytest.fixture
def multidir_tartex_obj(datadir, multidir_target):
    return TarTeX(
        [
            (Path(datadir) / "main.tex").as_posix(),
            "-v",
            "-s",
            "-o",
            multidir_target.as_posix(),
        ]
    )


@pytest.fixture
def src_files(datadir):
    """Return sorted list of files in source dir"""
    src_files = [
        str(Path(dname).relative_to(datadir) / f)
        for dname, _, files in os.walk(datadir)
        for f in files
    ]

    src_files.sort()  # Sort for comparison with tar output
    return src_files


class TestMultiDir:
    """Tests for LaTeX projects with files spread across multiple dirs"""

    def test_tar(self, src_files, multidir_tartex_obj):
        """Test tar file creation"""
        t = multidir_tartex_obj

        t.tar_files()
        output = t.tar_file_w_ext
        assert output.exists()

        with tar.open(output, "r") as rat:
            # Check if files in tarball have the same dir structure as src_files
            assert src_files == sorted(rat.getnames())

    def test_list(self, datadir):
        """Test printing list of files"""
        t = TarTeX(
            [
                (Path(datadir) / "main.tex").as_posix(),
                "-l",
                "-s",
                "-o",  # avoid conflict with tarballs from other tests
                (Path(datadir) / "multidir_list.tar.bz2").as_posix(),
            ]
        )
        t.tar_files()

        # Tar file must not be created with "-l"
        assert not t.tar_file_w_ext.exists()

    def test_only_check_success(self, datadir, capsys):
        t = TarTeX(
            [
                (Path(datadir) / "main.tex").as_posix(),
                "--only-check",
                "-o", # unique output to avoid conflicts with other tests
                (Path(datadir) / "multidir_check_ok.tar.gz").as_posix(),
            ]
        )
        t.tar_files()

        # Tar file must not be created with "--check"
        assert not t.tar_file_w_ext.exists()

        out_msg = capsys.readouterr().out
        assert "figures/peppers.png" in out_msg
        assert "All files needed for compilation included in tarball" in out_msg

    def test_check_fail_excl(self, datadir, capsys):
        """`--check` must fail when necessary image file is excluded from tarball"""
        t = TarTeX(
            [
                (Path(datadir) / "main.tex").as_posix(),
                "-o", # unique output to avoid conflicts with other tests
                (Path(datadir) / "multidir_check_fail.tar.gz").as_posix(),
                "--check",
                "-x",
                "*.png"
            ]
        )
        with pytest.raises(SystemExit) as exc:
            t.tar_files()

        assert exc.value.code == 1
        out_msg = capsys.readouterr().out
        assert "Files needed for compilation not included" in out_msg
        assert "peppers.png" in out_msg
