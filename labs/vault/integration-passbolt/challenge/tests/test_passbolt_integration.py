"""Tests structure lab 83 — intégration Passbolt.

Le serveur Passbolt nécessite une clé OpenPGP par utilisateur, ce qui
empêche un test automatisé "out of the box" (clé personnelle requise).
On vérifie ici la STRUCTURE du lab, conformément au pattern lab 82.
"""

from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]


def test_setup_script_exists():
    """Le script setup-passbolt.sh existe et est exécutable."""
    script = LAB_DIR / "setup-passbolt.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111, "setup-passbolt.sh doit être exécutable"


def test_setup_script_uses_podman():
    """Le script utilise Podman (cohérence avec la stack du repo)."""
    content = (LAB_DIR / "setup-passbolt.sh").read_text()
    assert "podman" in content
    assert "passbolt/passbolt" in content
    assert "mariadb" in content.lower()


def test_playbook_uses_passbolt_lookup():
    """playbook.yml utilise la collection anatomicjc.passbolt."""
    content = (LAB_DIR / "playbook.yml").read_text()
    assert "anatomicjc.passbolt.passbolt" in content


def test_playbook_uses_no_log():
    """no_log activé sur la tâche qui manipule le secret."""
    content = (LAB_DIR / "playbook.yml").read_text()
    assert "no_log: true" in content


def test_playbook_no_hardcoded_secret():
    """Aucun secret en clair dans le playbook."""
    content = (LAB_DIR / "playbook.yml").read_text().lower()
    forbidden = ["passbolt123", "demopass", "rootlab83"]
    for pattern in forbidden:
        assert pattern not in content, f"Secret en clair détecté : {pattern}"


def test_playbook_uses_passbolt_variables():
    """Le playbook utilise les variables passbolt_uri / passbolt_private_key."""
    content = (LAB_DIR / "playbook.yml").read_text()
    assert "passbolt_uri" in content
    assert "passbolt_private_key" in content
    assert "passbolt_passphrase" in content


def test_readme_mentions_alternative():
    """Le README explique le positionnement vs HashiCorp Vault."""
    readme = (LAB_DIR / "README.md").read_text()
    assert "passbolt" in readme.lower()
    assert "openpgp" in readme.lower() or "OpenPGP" in readme
