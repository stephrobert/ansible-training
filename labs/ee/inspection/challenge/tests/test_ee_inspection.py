"""Tests structurels lab 85 — Inspection d'EE."""

from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]


def test_inspect_script_exists():
    script = LAB_DIR / "inspect.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111


def test_inspect_script_uses_three_ees():
    content = (LAB_DIR / "inspect.sh").read_text()
    assert "creator-ee" in content
    assert "awx-ee" in content
    assert "community-ee-minimal" in content


def test_inspect_script_uses_ansible_navigator():
    content = (LAB_DIR / "inspect.sh").read_text()
    assert "ansible-navigator" in content


def test_inspect_script_documents_ansible_galaxy_collection_list():
    content = (LAB_DIR / "inspect.sh").read_text()
    assert "ansible-galaxy collection list" in content
