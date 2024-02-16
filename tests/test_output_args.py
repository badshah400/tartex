# vim:set et sw=4 ts=4:
"""
Test sanitisation of --output arg
"""

import os
import pytest
from pathlib import Path

from tartex.tartex import TarTeX


@pytest.fixture
def sample_tex():
    return "sample.tex"

def test_output_default(sample_tex):
    """
    Check correct tar suffix set when output arg ext is not specified
    """
    t = TarTeX([sample_tex, "-o", "main"])
    assert t.tar_file.name == "main.tar"

def test_output_nontar(sample_tex):
    """
    Check correct tar file name is set when output arg does have an extension
    but not one that matches .tar.?z
    """
    out = "main.foo.bar" # Output should be "main.foo.bar.tar.XX", not
                         # "main.foo.tar.XX"
    t = TarTeX([sample_tex, "-o", out])
    assert t.tar_file.name == out + ".tar"

def test_output_gz_eqv(sample_tex):
    """
    Check that the three kinds of output file names lead to same final tar file
    """
    common_opts = [sample_tex, "-o"]
    out = "main"
    t1 = TarTeX(common_opts + [out])
    t2 = TarTeX(common_opts + [out + ".gz"])
    t3 = TarTeX(common_opts + [out + ".tar.gz"])

    assert t1.tar_file == t2.tar_file
    assert t2.tar_file == t3.tar_file

def test_tilde_exp(sample_tex):
    """
    Check that '~' specified for output arg expands to user home
    """
    t = TarTeX([sample_tex, "-o", "~/main.tar.xz"])
    assert str(t.tar_file) == os.getenv("HOME") + "/main.tar"
