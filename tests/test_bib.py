# vim:set et sw=4 ts=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT
#
"""
Test inclusion and exclusion of .bib files
"""

import tarfile as tar

from tartex.tartex import TAR_DEFAULT_COMP, TarTeX


def test_bib(datadir, tmpdir):
    """Test if tar file contains .bib when -b is passed"""
    t = TarTeX(
        [
            str(datadir / "main_bib.tex"),
            "-b",
            "-s",
            "-v",
            "-o",
            f"{tmpdir!s}/main_bib",
        ]
    )
    t.tar_files()
    with tar.open(t.tar_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}")) as f:
        assert "refs.bib" in f.getnames()  # Check: .bib file is in tarball
        # Check main_bib.bbl file is in tarball even though not in srcdir
        assert "main_bib.bbl" in f.getnames()
