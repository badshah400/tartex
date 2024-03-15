# vim:set et sw=4 ts=4 tw=79:
"""
Tests for package list inclusion
"""

import json
import tarfile as tar

from tartex.tartex import TAR_DEFAULT_COMP, TarTeX


def test_float_pkg(datadir, tmpdir, capsys):
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
    assert "2 files" in capsys.readouterr().out
    with tar.open(
        f"{tmpdir!s}/packagelist.tar.{TAR_DEFAULT_COMP}", mode="r"
    ) as f:
        assert "TeXPackages.json" in f.getnames()

    pkgjson = json.loads(t.pkglist)
    assert "float" in pkgjson["System"]
    assert pkgjson["Local"] == []
