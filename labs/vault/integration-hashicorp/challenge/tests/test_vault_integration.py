"""Tests structure du lab 82 — intégration HashiCorp Vault / OpenBao."""

from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]


def test_setup_script_present():
    """Le script setup-vault.sh est présent et exécutable."""
    script = LAB_ROOT / "setup-vault.sh"
    assert script.exists()
    assert script.stat().st_mode & 0o111  # bit exécutable


def test_setup_script_supports_openbao():
    """Le script supporte OpenBao via variable IMAGE."""
    content = (LAB_ROOT / "setup-vault.sh").read_text()
    assert "IMAGE" in content
    assert "hashicorp/vault" in content or "openbao/openbao" in content


def test_playbook_uses_hashi_vault_lookup():
    """Le playbook utilise la lookup community.hashi_vault."""
    content = (LAB_ROOT / "playbook.yml").read_text()
    assert "community.hashi_vault" in content
    assert "lookup" in content


def test_playbook_uses_kv_v2():
    """Utilise le moteur KV v2 (recommandé Vault moderne)."""
    content = (LAB_ROOT / "playbook.yml").read_text()
    assert "vault_kv2_get" in content


def test_playbook_uses_engine_mount_point():
    """Engine mount point 'secret' explicite."""
    content = (LAB_ROOT / "playbook.yml").read_text()
    assert "engine_mount_point" in content


def test_no_secret_in_clear_in_playbook():
    """Aucun secret en clair dans le playbook (ils viennent de Vault)."""
    content = (LAB_ROOT / "playbook.yml").read_text()
    # On vérifie qu'on ne trouve pas un pattern de secret en dur
    assert "VaultPassLab82" not in content   # le secret est dans Vault, pas en clair
    assert "vault_api_xyz_lab82" not in content
