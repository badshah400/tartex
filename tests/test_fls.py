# vim:set et sw=4 ts=4:

"""
Tests for when source dir has .fls file
"""

import pytest

from tartex.tartex import TarTeX


def test_fls_main_arg(datadir, capsys):
    """User passes a .fls filename as input"""
    fls_name = "main.fls"
    t = TarTeX(
        [str(datadir / fls_name), "-o", str(datadir), "-x", "*.bbl", "-bs"],
    )
    assert t.tar_file.name == fls_name.replace(".fls", ".tar")
    # Note that this will throw because the .bbl file marked as INPUT in
    # pre-generated .fls file does not exist in source dir
    with pytest.raises(FileNotFoundError) as exc:
        t.tar_files()

    assert exc.match("No such file or directory:")
