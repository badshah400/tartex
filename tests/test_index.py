# vim:set et sw=4 ts=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#
"""
Test inclusion and exclusion of .ind files
"""

import tarfile as tar

import pytest

from tartex.tartex import TAR_DEFAULT_COMP, TarTeX


@pytest.fixture
def default_args(datadir, tmpdir):
    return [
        str(datadir / "test_index.tex"),
        "-s",
        "-v",
        "-o",
        f"{tmpdir!s}/test_index.tar.{TAR_DEFAULT_COMP}",
    ]


class TestIndex:

    """Test to verify handling of missing .ind file"""

    def test_ind(self, default_args):
        """
        Check: By default tar file must contain '.ind' when it is not excluded
        """
        t = TarTeX(default_args)
        t.tar_files()
        with tar.open(t.tar_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}")) as f:
            # Check test_index.ind file is in tarball even though not in srcdir
            assert "test_index.ind" in f.getnames()
            # Check user/group name attributes
            for attr in ["gname", "uname"]:
                assert (
                    f.getmember("test_index.ind").get_info()[attr]
                    == f.getmember(t.main_file.name).get_info()[attr]
                )

    def test_ind_excl(self, default_args):
        """
        Check: tar file must not contain '.ind' when it is asked to be excluded
        """
        args = [*default_args, "-x", "*.ind"]
        t = TarTeX(args)
        t.tar_files()
        with tar.open(t.tar_file.with_suffix(f".tar.{TAR_DEFAULT_COMP}")) as f:
            # Check test_index.ind file is not in tarball
            assert "test_index.ind" not in f.getnames()
