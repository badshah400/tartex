# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT
#
"""Tests for tarball generation from basic latex files"""
import tarfile as tar
from pathlib import Path
import pytest
from tartex.tartex import TarTeX, TAR_DEFAULT_COMP


@pytest.fixture
def default_target(datadir):
    return Path(datadir) / "test"


@pytest.fixture
def default_tartex_obj(datadir, default_target):
    return TarTeX(
        [
            (Path(datadir) / "basic_latex.tex").as_posix(),
            "-o",
            default_target.as_posix(),
        ]
    )


class TestBasicLaTeX:
    """Tests checking tar file generation from a basic latex file"""

    def test_gen_tar(self, default_target, default_tartex_obj, capsys):
        """Should include a single file in tarball"""
        output = default_target.with_suffix(".tar.gz")
        t = default_tartex_obj
        t.tar_files()
        assert output.exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1


# These tests involve repeatedly compiling LaTeX files, thus can be slow
@pytest.mark.slow
class TestTarConflict:
    """Tests checking resolutions for tar file name conflicts"""

    def test_resolve_default(self, default_tartex_obj, monkeypatch):
        """Test when user response is not workable"""
        t_con = default_tartex_obj
        t_con.tar_files()

        # Monkeypatch empty response for input
        monkeypatch.setattr("builtins.input", lambda resolve: "")

        # Trying to create tar file again will lead to conflic res dialog
        # Blank user input (from monkeypatch) will raise SystemExit
        with pytest.raises(SystemExit) as exc:
            t_con.tar_files()

        assert "Not overwriting existing tar file" in exc.value.code

    def test_resolve_quit(self, default_tartex_obj, monkeypatch):
        """Test when user response is not workable"""
        t_con = default_tartex_obj
        t_con.tar_files()

        # Monkeypatch empty response for input
        monkeypatch.setattr("builtins.input", lambda resolve: "q")

        # Trying to create tar file again will lead to conflic res dialog
        # Blank user input (from monkeypatch) will raise SystemExit
        with pytest.raises(SystemExit) as exc:
            t_con.tar_files()

        assert "Not overwriting existing tar file" in exc.value.code

    def test_resolve_overwrite(self, default_tartex_obj, monkeypatch):
        """Test overwrite resolution"""
        t_con = default_tartex_obj
        t_con.tar_files()

        # Monkeypatch empty response for input
        monkeypatch.setattr("builtins.input", lambda resolve: "o")
        t_con.tar_files()
        output = t_con.tar_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}")
        assert output.exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_resolve_newname_good(self, default_tartex_obj, tmpdir, monkeypatch):
        """Test entering new name that works"""
        t_con = default_tartex_obj
        t_con.tar_files()

        output = str(tmpdir / "new.tar.gz")
        # Monkeypatch responses for choosing a new file name
        user_inputs = iter(['c', output])
        monkeypatch.setattr("builtins.input", lambda resolve: next(user_inputs))
        t_con.tar_files()
        assert Path(output).exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_resolve_newname_bad(self, default_tartex_obj, tmpdir, monkeypatch):
        """Test overwrite resolution"""
        t_con = default_tartex_obj
        t_con.tar_files()

        output = str(tmpdir / "test.tar.gz")
        assert Path(output).exists() is True

        # Monkeypatch responses for choosing file name same as original
        user_inputs = iter(['c', output])
        monkeypatch.setattr("builtins.input", lambda resolve: next(user_inputs))
        with pytest.raises(SystemExit) as exc:
            t_con.tar_files()

        assert "New name entered is also the same" in exc.value.code
