# vim:set et sw=4 ts=4:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <atrib@duck.com>
#
# SPDX-License-Identifier: MIT
#

"""
Tests for package list inclusion
"""

import json
import tarfile as tar

from tartex.tartex import TarTeX
from tartex.utils.tar_utils import TAR_DEFAULT_COMP


def test_float_pkg(datadir, tmpdir, capsys, join_linebreaks):
    """
    Test 'packages.json' for float package included from test_packages
    """
    t = TarTeX(
        [
            str(datadir / "main.tex"),
            "-s",
            "-p",
            "-o",
            f"{tmpdir!s}/packagelist",
        ]
    )
    t.tar_files()
    with tar.open(
        f"{tmpdir!s}/packagelist.tar.{TAR_DEFAULT_COMP}", mode="r"
    ) as f:
        assert 2 == len(f.getnames())
        assert "TeXPackages.json" in f.getnames()

    pkgjson = json.loads(t.pkglist)
    assert "float" in pkgjson["System"]
    assert pkgjson["Local"] == []
