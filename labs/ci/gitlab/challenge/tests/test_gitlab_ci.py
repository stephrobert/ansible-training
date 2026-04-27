"""Tests structure du pipeline GitLab CI (lab 70)."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
GITLAB_CI = LAB_ROOT / ".gitlab-ci.yml"


def test_gitlab_ci_present():
    assert GITLAB_CI.exists()


def test_pipeline_has_lint_and_test_stages():
    config = yaml.safe_load(GITLAB_CI.read_text())
    stages = config.get("stages", [])
    assert "lint" in stages
    assert "test" in stages


def test_ansible_lint_job_present():
    config = yaml.safe_load(GITLAB_CI.read_text())
    assert "ansible-lint" in config


def test_molecule_test_uses_parallel_matrix():
    """Matrice multi-distros / multi-versions via parallel:matrix."""
    config = yaml.safe_load(GITLAB_CI.read_text())
    job = config["molecule-test"]
    assert "parallel" in job
    matrix = job["parallel"]["matrix"]
    assert isinstance(matrix, list)
    assert len(matrix) >= 3, "Au moins 3 combinaisons distro × version"


def test_molecule_test_depends_on_lint():
    config = yaml.safe_load(GITLAB_CI.read_text())
    needs = config["molecule-test"].get("needs", [])
    assert "ansible-lint" in needs


def test_release_only_on_tag():
    """Le job release n'est déclenché que sur un tag Git."""
    config = yaml.safe_load(GITLAB_CI.read_text())
    rules = config["release"]["rules"]
    assert any("CI_COMMIT_TAG" in str(r.get("if", "")) for r in rules)


def test_no_secrets_in_yaml():
    """Pas de tokens / secrets en clair dans .gitlab-ci.yml."""
    content = GITLAB_CI.read_text().lower()
    forbidden = ["password:", "secret:", "api_key=", "token="]
    for f in forbidden:
        assert f not in content, f"Mot interdit '{f}' dans .gitlab-ci.yml"
