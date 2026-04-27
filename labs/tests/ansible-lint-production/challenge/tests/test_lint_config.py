"""Tests structure config ansible-lint + yamllint + pre-commit (lab 68)."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]


def test_ansible_lint_config_present():
    assert (LAB_ROOT / ".ansible-lint").exists()


def test_yamllint_config_present():
    assert (LAB_ROOT / ".yamllint").exists()


def test_pre_commit_config_present():
    assert (LAB_ROOT / ".pre-commit-config.yaml").exists()


def test_ansible_lint_uses_production_profile():
    config = yaml.safe_load((LAB_ROOT / ".ansible-lint").read_text())
    assert config.get("profile") == "production", (
        "Le profil doit être 'production' pour le contrôle le plus strict"
    )


def test_pre_commit_includes_ansible_lint():
    content = (LAB_ROOT / ".pre-commit-config.yaml").read_text()
    assert "ansible-lint" in content
    assert "yamllint" in content
    assert "production" in content


def test_pre_commit_blocks_secrets():
    content = (LAB_ROOT / ".pre-commit-config.yaml").read_text()
    assert "detect-private-key" in content, (
        "Hook detect-private-key recommandé pour bloquer les fuites"
    )


def test_yamllint_disables_truthy_yes_no():
    """yamllint doit forcer true/false (YAML 1.2 strict)."""
    config = yaml.safe_load((LAB_ROOT / ".yamllint").read_text())
    truthy_rule = config["rules"].get("truthy", {})
    if isinstance(truthy_rule, dict):
        allowed = truthy_rule.get("allowed-values", [])
        assert "true" in allowed and "false" in allowed
        assert "yes" not in allowed and "no" not in allowed
