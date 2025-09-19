# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""Tests for tarball generation from basic latex files"""

import json
import logging
import os
import tarfile as tar
from pathlib import Path
from tartex.utils.hash_utils import HASH_METHOD

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


class TestBasicLaTeX:
    """Tests checking tar file generation from a basic latex file"""

    def test_list_only(self, datadir, default_target, capsys):
        """Test `--list` and `--dry-run` options which _do not_ produce tarballs"""
        output = default_target.with_suffix(".tar.gz")
        for opt in ["-l", "--list", "--dry-run"]:
            t = TarTeX([(Path(datadir) / "basic_latex.tex").as_posix(), opt])
            t.tar_files()
            assert t.args.list
            assert not output.exists()
            assert "basic_latex.tex" in capsys.readouterr().out.strip()

    def test_gen_tar(self, default_target, default_tartex_obj):
        """Should include a single file in tarball"""
        output = default_target.with_suffix(".tar.gz")
        t = default_tartex_obj("basic_latex.tex")
        t.tar_files()
        assert output.exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_gen_tar_no_suffix(self, default_target, default_tartex_obj):
        """Should include a single file in tarball even though main file has no
        .tex or .fls suffix
        """
        output = default_target.with_suffix(".tar.gz")
        t = default_tartex_obj("basic_latex")
        t.tar_files()
        assert output.exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_diff_target_dir(self, tmpdir, datadir):
        # Make a new dir inside tmpdir
        destdir = tmpdir / "dest"
        os.mkdir(destdir)
        t = TarTeX(
            [
                (Path(datadir) / "basic_latex.tex").as_posix(),
                "-v",
                "-s",
                "-o",
                str(destdir / "output.tar.gz"),
            ]
        )
        t.tar_files()
        assert t.tar_file_w_ext.exists()

    def test_incl_pdf(self, datadir):
        """
        Test option `--with-pdf` for inclusion of pdf in tarball
        """
        t = TarTeX(
            [
                (Path(datadir) / "basic_latex.tex").as_posix(),
                "--with-pdf",
                "-o",
                f"{datadir}/basic_latex_with_pdf.tar.gz",
            ]
        )
        t.tar_files()
        with tar.open(t.tar_file_w_ext) as f:
            assert len(f.getnames()) == 2
            assert t.main_file.with_suffix(".pdf").name in f.getnames()

    def test_verbose_debug(self, datadir):
        """
        Test verbose value set by -vv option
        """
        t = TarTeX([(Path(datadir) / "basic_latex.tex").as_posix(), "-vv"])
        assert t.args.verbose == 2

class TestCache:
    """Tests involving cache generation, retrieval, and update"""

    def test_cache_gen(self, datadir):
        """
        Test cache file is generated when tartex is first run
        """
        t = TarTeX(
            [
                str(datadir / "basic_latex.tex"),
                "-v",
                "-o",
                str(datadir / "cache_gen.tar.gz"),
            ]
        )
        t.tar_files()
        assert t.tar_file_w_ext.exists()
        assert t.filehash_cache.exists()
        with open(t.filehash_cache, "r") as _c:
            _j = json.load(_c)
            assert "basic_latex.tex" in _j["input_files"]
            assert not _j["streams"]  # _j["streams"] is empty list

    def test_cache_retrieve(self, datadir):
        """
        Test cache file is untouched when tartex is rerun without changes to
        input files
        """
        t = TarTeX(
            [
                str(datadir / "basic_latex.tex"),
                "-v",
                "--overwrite",
                "-o",
                str(datadir / "cache_ret.tar.gz"),
            ]
        )
        t.tar_files()
        assert t.filehash_cache.exists()
        mtime = int(os.path.getmtime(t.filehash_cache))
        t.tar_files()  # run mustn't touch cache, as no input files changed
        assert int(os.path.getmtime(t.filehash_cache)) == mtime

    def test_cache_update(self, datadir):
        """
        Test cache file is updated when tartex is run after input files change
        """
        t = TarTeX(
            [
                str(datadir / "basic_latex.tex"),
                "-v",
                "--overwrite",
                "-o",
                str(datadir / "cache_up.tar.gz"),
            ]
        )

        # First run
        t.tar_files()
        assert t.filehash_cache.exists()
        mtime = os.path.getmtime(t.filehash_cache)
        with open(t.filehash_cache, "r") as _c:
            _j = json.load(_c)

        # Modify file
        with open(t.main_file, "a") as _f:
            _f.write("\n")

        # Second run
        t.tar_files()

        assert os.path.getmtime(t.filehash_cache) != mtime
        assert (
            _j["input_files"][t.main_file.name]
            != HASH_METHOD(t.main_file.read_bytes()).hexdigest()
        )
        with open(t.filehash_cache, "r") as _c:
            _j = json.load(_c)
        assert (
            _j["input_files"][t.main_file.name]
            == HASH_METHOD(t.main_file.read_bytes()).hexdigest()
        )

    def test_cache_force_recompile(self, datadir):
        """
        Test cache file is untouched when tartex is run with `-F`
        """
        t = TarTeX(
            [
                str(datadir / "basic_latex.tex"),
                "-v",
                "-F",
                "-o",
                str(datadir / "cache_recompile.tar.gz"),
            ]
        )
        t.tar_files()
        assert not t.filehash_cache.exists()

# These tests involve repeatedly compiling LaTeX files, thus can be slow
@pytest.mark.slow
class TestTarConflict:
    """Tests checking resolutions for tar file name conflicts"""

    def test_sol_default(
        self,
        default_target,
        default_tartex_obj,
        capsys,
        monkeypatch,
        join_linebreaks,
    ):
        """Test default (empty) user response"""
        t_con = default_tartex_obj("basic_latex.tex")
        t_con.tar_files()

        # Monkeypatch empty response for input
        monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "")

        # Trying to create tar file again will lead to conflict res dialog
        # Blank user input (from monkeypatch) will raise SystemExit
        with pytest.raises(SystemExit) as exc:
            t_con.tar_files()

        # Original output must still exist
        assert default_target.with_suffix(".tar.gz").exists() is True

        assert "Not overwriting existing tar file" in join_linebreaks(
            capsys.readouterr().err
        )
        assert exc.value.code == 1

    def test_sol_quit(
        self,
        default_target,
        default_tartex_obj,
        capsys,
        monkeypatch,
        join_linebreaks,
    ):
        """Test when user response is 'q'"""
        t_con = default_tartex_obj("basic_latex.tex")
        t_con.tar_files()

        # Monkeypatch empty response for input
        monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "q")

        # Trying to create tar file again will lead to conflic res dialog
        # Blank user input (from monkeypatch) will raise SystemExit
        with pytest.raises(SystemExit) as exc:
            t_con.tar_files()

        # Original output must still exist
        assert default_target.with_suffix(".tar.gz").exists() is True

        assert "Not overwriting existing tar file" in join_linebreaks(
            capsys.readouterr().err
        )
        assert exc.value.code == 1

    def test_sol_overwrite(self, default_tartex_obj, monkeypatch):
        """Test overwrite resolution"""
        t_con = default_tartex_obj("basic_latex.tex")
        t_con.tar_files()

        # Monkeypatch empty response for input
        monkeypatch.setattr("rich.prompt.Prompt.ask", lambda _: "o")
        t_con.tar_files()
        output = t_con.tar_file_w_ext
        assert output.exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_sol_newname_ok(
        self, default_target, default_tartex_obj, tmpdir, monkeypatch
    ):
        """Test entering new name that works"""
        t_con = default_tartex_obj("basic_latex.tex")
        t_con.tar_files()

        output = str(tmpdir / "new.tar.gz")
        # Monkeypatch responses for choosing a new file name
        user_inputs = iter(["c", output])
        monkeypatch.setattr(
            "rich.prompt.Prompt.ask", lambda _: next(user_inputs)
        )
        t_con.tar_files()

        # Original output must still exist
        assert default_target.with_suffix(".tar.gz").exists() is True

        assert Path(output).exists() is True
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_sol_newname_old(
        self, default_tartex_obj, tmpdir, capsys, monkeypatch, join_linebreaks
    ):
        """Test error when entering new name that is same as the old name"""
        t_con = default_tartex_obj("basic_latex.tex")
        t_con.tar_files()

        output = str(tmpdir / "test.tar.gz")

        # Monkeypatch responses for choosing file name same as original
        user_inputs = iter(["c", output])
        monkeypatch.setattr(
            "rich.prompt.Prompt.ask", lambda _: next(user_inputs)
        )
        with pytest.raises(SystemExit) as exc:
            t_con.tar_files()

        assert "New name entered is also the same" in join_linebreaks(
            capsys.readouterr().err
        )
        assert exc.value.code == 1
        # Original output must still exist
        assert Path(output).exists() is True

    def test_sol_newext(self, default_tartex_obj, tmpdir, monkeypatch):
        """Test new name with just the file ext changed"""
        t_con = default_tartex_obj("basic_latex.tex")
        t_con.tar_files()

        output = str(tmpdir / "test.tar.gz")
        assert Path(output).exists() is True

        output = output.replace(".gz", ".xz")
        # Monkeypatch responses for choosing file name same as original
        user_inputs = iter(["c", output])
        monkeypatch.setattr(
            "rich.prompt.Prompt.ask", lambda _: next(user_inputs)
        )
        t_con.tar_files()
        assert Path(output).exists() is True
        assert t_con.tar_ext == "xz"
        with tar.open(output) as rat:
            assert len(rat.getnames()) == 1

    def test_option_overwrite(
        self, caplog, datadir, default_target, default_tartex_obj
    ):
        """Should include a single file in tarball"""
        output = default_target.with_suffix(".tar.gz")
        t = default_tartex_obj("basic_latex.tex")
        t.tar_files()
        q = TarTeX(
            [
                (Path(datadir) / "basic_latex.tex").as_posix(),
                "--overwrite",
                "-o",
                default_target.as_posix(),
            ]
        )
        q.tar_files()
        assert output.exists() is True
        caplog.set_level(logging.WARNING)
        out_mess = caplog.text
        assert "overwriting existing" in out_mess.lower()

class TestOnlyCheckBasic:
    def test_only_check_success(self, capsys, datadir):
        """Use `--only-check` to report successful inclusion of single file"""
        t = TarTeX(
            [
                (Path(datadir) / "basic_latex.tex").as_posix(),
                "--only-check",
                "-o",
                (Path(datadir) / "basic_latex_check.tar.gz").as_posix(),
            ]
        )
        t.tar_files()
        assert not t.tar_file_w_ext.exists()
        assert "All files needed for compilation included" in capsys.readouterr().out

    def test_check_warn_pdf(self, capsys, datadir):
        """Warn when `--only-check` finds unnecessary files to be included"""
        t = TarTeX(
            [
                (Path(datadir) / "basic_latex.tex").as_posix(),
                "--only-check",
                "--with-pdf",
                "-o",
                (Path(datadir) / "basic_latex_warn.tar.xz").as_posix(),
            ]
        )
        t.tar_files()
        assert not t.tar_file_w_ext.exists()
        msg_out = capsys.readouterr().out
        assert "Files not essential to compilation" in msg_out
        assert "All files needed for compilation" in msg_out
