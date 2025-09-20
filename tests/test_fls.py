# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""
Tests for when source dir has .fls file
"""

import tarfile as tar

import pytest

from tartex.tartex import TarTeX

@pytest.fixture
def flsfile():
    """Default fls file name"""
    return "main.fls"


@pytest.fixture
def tartex_obj(datadir, flsfile):
    """Default tartex object with flsfile as input"""
    return TarTeX(
        [str(datadir / flsfile), "-o", str(datadir), "-bs"],
    )


class TestUseFls:
    """Tests for using in-project fls file as main input file"""

    def test_fls_main_arg(self, tartex_obj, flsfile):
        """User passes a .fls filename as input"""
        t = tartex_obj
        assert t.tar_file_w_ext.stem == flsfile.replace(".fls", ".tar")


    def test_fls_main_arg_noext(self, datadir, flsfile):
        """
        User passes a file name with no extension but tartex should find .fls file
        """
        flsfile_noext = flsfile.removesuffix(".fls")
        t = TarTeX(
            [str(datadir / flsfile_noext), "-o", str(datadir), "-b"],
        )
        t.tar_files()
        assert t.tar_file_w_ext.name == f"{flsfile_noext}.tar.{t.tar_ext}"
        with tar.open(f"{t.tar_file_w_ext}") as f:
            assert len(f.getnames()) == 2


    def test_fls_missing_bbl(self, tartex_obj, flsfile):
        """
        Verify that missing .bbl file is omitted from tarball and the call to
        tar_files() does not cause an exception
        """
        tartex_obj.tar_files()

        with tar.open(f"{tartex_obj.tar_file_w_ext}") as f:
            assert flsfile.replace(".fls", ".bbl") not in f.getnames()


    def test_no_permission(self, datadir, flsfile, caplog):
        """Setting output to a dir without write perms will print appropriate msg"""
        t = TarTeX([str(datadir / flsfile), "-o", "/test_no_perms.tar.bz2", "-v"])
        with pytest.raises(SystemExit) as exc:
            t.tar_files()

        assert exc.value.code == 1
        err_msg = caplog.text.lower()
        assert "critical" in err_msg
        assert "permission denied" in err_msg

    def test_fls_recompile(self, datadir, flsfile):
        """Forcing a LaTeX recompile ensures .bbl is included"""
        t = TarTeX([str(datadir / flsfile), "-o", str(datadir), "-b", "-F"])
        t.tar_files()

        with tar.open(f"{t.tar_file_w_ext}") as f:
            assert flsfile.replace(".fls", ".bbl") in f.getnames()

    def test_fls_no_pdf(self, datadir, flsfile, caplog):
        """Silently skip missing pdf when `--with-pdf is used`"""
        t = TarTeX(
            [
                str(datadir / flsfile),
                "-o",
                str(datadir / "missing_pdf.tar.xz"),
                "-v",
                "--with-pdf"
            ]
        )
        t.tar_files()
        assert t.tar_file_w_ext.exists()
        with tar.open(f"{t.tar_file_w_ext}") as f:
            assert t.main_file.with_suffix(".pdf") not in f.getnames()
        assert "Skipping pdf not found" in caplog.text

class TestFlsNoCache:
    """Check that no cache is touched when using .fls file directly"""

    def test_fls_no_cache(self, datadir, flsfile):
        """
        cache file must not be generated when using .fls directly
        """
        flsfile_noext = flsfile.removesuffix(".fls")
        t = TarTeX(
            [
                str(datadir / flsfile_noext),
                "-o",
                str(datadir / "fls_no_cache"),
                "-b"
            ],
        )
        t.tar_files()
        assert not t.filehash_cache.exists()
