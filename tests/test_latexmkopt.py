# vim:set et sw=4 ts=4 tw=80:
"""
Tests for passing various TeX processors to latexmk
"""

import pytest

from tartex.tartex import TarTeX, TAR_DEFAULT_COMP

@pytest.fixture
def latex_file(datadir):
    return datadir/"latexmk_opts.tex"

@pytest.fixture
def basic_opts(latex_file, datadir, tmpdir):
    return [str(latex_file),
            "-s",
            "-v",
            "-o",
            str(tmpdir / f"lmk.tar.{TAR_DEFAULT_COMP}")]


class TestLatexmkOpts:

    """Tests to check various tex processors for latexmk"""

    def test_auto_pdf(self, basic_opts):
        """Check: Automatic processing should use '-pdf'
        """
        t = TarTeX(basic_opts)
        t.tar_files()
        assert t.tar_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}").exists()

    def test_ps(self, basic_opts):
        """Check: Processing using -ps
        """
        basic_opts.extend(["--latexmk_tex", "ps"])
        t = TarTeX(basic_opts)
        t.tar_files()

    def test_pdflua(self, basic_opts):
        """Check: Processing using -pdflua
        """
        basic_opts.extend(["--latexmk_tex", "pdflua"])
        t = TarTeX(basic_opts)
        t.tar_files()
