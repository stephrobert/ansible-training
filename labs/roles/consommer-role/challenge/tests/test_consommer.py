"""Tests structure des 3 patterns de consommation de rôle."""

from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
PLAYBOOK = LAB_ROOT / "playbook.yml"


def test_playbook_present():
    assert PLAYBOOK.exists()


def test_uses_roles_classic_syntax():
    content = PLAYBOOK.read_text()
    assert "roles:" in content


def test_uses_import_role():
    content = PLAYBOOK.read_text()
    assert "import_role" in content or "ansible.builtin.import_role" in content


def test_uses_include_role():
    content = PLAYBOOK.read_text()
    assert "include_role" in content or "ansible.builtin.include_role" in content


def test_include_role_has_conditional():
    """include_role utilisé avec when: pour démontrer la nature dynamique."""
    content = PLAYBOOK.read_text()
    # Cherche un bloc include_role suivi (en quelques lignes) d'un when
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "include_role" in line:
            # Chercher dans les 10 lignes suivantes un when
            for j in range(i, min(i + 15, len(lines))):
                if "when:" in lines[j]:
                    return  # OK
    raise AssertionError("include_role doit être combiné avec when: pour démontrer le pattern dynamique")


def test_at_least_3_plays():
    """Le playbook démontre les 3 patterns dans 3 plays distincts."""
    content = PLAYBOOK.read_text()
    play_count = content.count("- name:") - content.count("    - name:")  # estimation grossière
    # Plus simple : compter les " hosts:" en début de ligne
    lines = content.split("\n")
    plays = sum(1 for l in lines if l.startswith("  hosts:") or l.startswith("- hosts:"))
    plays += sum(1 for l in lines if l.startswith("hosts:"))
    assert plays >= 3, f"3 plays attendus pour démontrer les 3 patterns, vu : {plays}"
