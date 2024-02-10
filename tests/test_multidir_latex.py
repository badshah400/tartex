# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT

"""Tests for LaTeX project consisting of multiple dirs"""

import os
import tarfile as tar
from pathlib import Path

import pytest

from tartex.tartex import TarTeX, TAR_DEFAULT_COMP


@pytest.fixture
def multidir_target(datadir):
    return Path(datadir) / "multi"


@pytest.fixture
def multidir_tartex_obj(datadir, multidir_target):
    return TarTeX(
        [
            (Path(datadir) / "main.tex").as_posix(),
            "-o",
            multidir_target.as_posix(),
        ]
    )


class TestMultiDir:
    """Tests for LaTeX projects with files spread across multiple dirs"""

    def test_tar(self, datadir, multidir_tartex_obj):
        """Test tar file creation"""
        t = multidir_tartex_obj
        src_files = []

        src_files = [str(Path(dname).relative_to(datadir) / f)
                     for dname, _, files in os.walk(datadir)
                     for f in files]

        src_files.sort()  # Sort for comparison with tar output

        t.tar_files()
        output = t.tar_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}")
        assert output.exists()

        with tar.open(output, "r") as rat:
            # Check if files in tarball have the same dir structure as src_files
            assert src_files == sorted(rat.getnames())
