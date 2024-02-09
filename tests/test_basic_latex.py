# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT
#
"""Tests for tarball generation from basic latex files"""
import tarfile as tar
from pathlib import Path
import pytest
from tartex.tartex import TarTeX


class TestBasicLaTeX:
    """Tests checking tar file generation from a basic latex file"""
    def test_gen_tar(self, datadir, tmpdir, capsys):
        """Should include a single file in tarball"""
        output = Path(f"{tmpdir}/test.tar.gz")
        t = TarTeX([(Path(datadir) / "basic_latex.tex").as_posix(),
                    "-o",
                    output.as_posix()])
        t.tar_files()
        print(capsys.readouterr().out)
        assert output.exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1
