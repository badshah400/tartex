# vim: set ai et ts=4 sw=4 tw=80:
# SPDX-FileCopyrightText: 2024-present Atri Bhattacharya <A.Bhattacharya@uliege.be>
#
# SPDX-License-Identifier: MIT

"""Common fixtures"""

import pytest
from tartex.tartex import TarTeX

@pytest.fixture
def sample_texfile():
    """Pytest fixture: TarTeX with just a tex file for parameter"""
    t = TarTeX(["some_file.tex"])
    return t
