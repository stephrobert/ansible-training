"""Tests structure de l'audit checklist (lab 75)."""

from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
CHECKLIST = LAB_ROOT / "AUDIT_CHECKLIST.md"


def test_checklist_present():
    assert CHECKLIST.exists()


def test_checklist_covers_maintainer():
    content = CHECKLIST.read_text().lower()
    assert "mainteneur" in content or "maintainer" in content


def test_checklist_covers_security():
    content = CHECKLIST.read_text().lower()
    assert "sécurité" in content or "security" in content
    assert "secret" in content


def test_checklist_covers_tests():
    content = CHECKLIST.read_text().lower()
    assert "molecule" in content
    assert "ansible-lint" in content


def test_checklist_covers_idempotence():
    content = CHECKLIST.read_text().lower()
    assert "idempotence" in content


def test_checklist_covers_argument_specs():
    content = CHECKLIST.read_text()
    assert "argument_specs" in content


def test_checklist_has_score():
    content = CHECKLIST.read_text()
    assert "score" in content.lower()


def test_at_least_25_checkpoints():
    """Au moins 25 points dans la checklist (richesse d'audit)."""
    content = CHECKLIST.read_text()
    count = content.count("- [ ]")
    assert count >= 25, f"Au moins 25 checkpoints attendus, vu : {count}"
