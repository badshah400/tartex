# vim:set et sw=4 ts=4:
"""
Tests for bash completion printing and installing
"""

from pathlib import Path
import pytest

from tartex._completion import BashCompletion, APPNAME
from tartex.tartex import TarTeX

def test_print(capsys):
    """Test output of print is not empty"""
    with pytest.raises(SystemExit) as exc:
        TarTeX(["--completion"])

    assert "bash" in capsys.readouterr().out
    assert exc.value.code == 0

def test_install(capsys, monkeypatch, tmpdir):
    """Test installed completions file"""
    monkeypatch.setenv("HOME", str(tmpdir))
    with pytest.raises(SystemExit) as exc:
        TarTeX(["--bash-completion"])

    assert exc.value.code == 0
    bc = BashCompletion()
    bc.print()
    compl_file = Path.home() / bc.install_dir / APPNAME
    assert str(compl_file.parent) in capsys.readouterr().out
    assert compl_file.exists()
    assert compl_file.read_text(encoding="utf-8") == bc.data
