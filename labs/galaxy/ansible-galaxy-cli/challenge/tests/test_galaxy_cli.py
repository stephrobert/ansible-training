"""Tests structure du cheatsheet ansible-galaxy CLI (lab 73)."""

import subprocess
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
CHEATSHEET = LAB_ROOT / "cheatsheet.md"


def test_cheatsheet_present():
    assert CHEATSHEET.exists()


def test_cheatsheet_covers_init():
    content = CHEATSHEET.read_text()
    assert "ansible-galaxy role init" in content


def test_cheatsheet_covers_install():
    content = CHEATSHEET.read_text()
    assert "ansible-galaxy role install" in content
    assert "ansible-galaxy collection install" in content


def test_cheatsheet_covers_list():
    content = CHEATSHEET.read_text()
    assert "ansible-galaxy role list" in content
    assert "ansible-galaxy collection list" in content


def test_cheatsheet_covers_publish():
    content = CHEATSHEET.read_text()
    assert "ansible-galaxy collection publish" in content
    assert "ansible-galaxy collection build" in content


def test_cheatsheet_covers_verify():
    content = CHEATSHEET.read_text()
    assert "ansible-galaxy collection verify" in content


def test_ansible_galaxy_command_works():
    """ansible-galaxy --version fonctionne (sanity check)."""
    result = subprocess.run(
        ["ansible-galaxy", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
