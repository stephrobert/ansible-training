"""Tests structurels lab 96 — pipeline CI collection."""

import re

import yaml
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = LAB_DIR / "challenge"
GH_WORKFLOW = CHALLENGE_DIR / ".github" / "workflows" / "ansible-test.yml"
GITLAB_CI = CHALLENGE_DIR / ".gitlab-ci.yml"


def test_github_workflow_exists():
    assert GH_WORKFLOW.is_file(), (
        f"{GH_WORKFLOW} absent — créez le workflow GitHub Actions."
    )


def test_github_workflow_has_global_permissions_empty():
    content = GH_WORKFLOW.read_text()
    assert "permissions: {}" in content, (
        "permissions: {} absent au niveau global du workflow."
    )


def test_github_workflow_has_persist_credentials_false():
    content = GH_WORKFLOW.read_text()
    assert "persist-credentials: false" in content, (
        "persist-credentials: false absent — risque d'exfiltration du token."
    )


def test_github_workflow_pins_actions_by_sha():
    """Toutes les actions externes doivent être pinnées par SHA 40 chars hex."""
    content = GH_WORKFLOW.read_text()
    uses_lines = re.findall(r"uses:\s+(\S+/\S+@\S+)", content)
    for line in uses_lines:
        ref = line.split("@")[1].split()[0]
        assert len(ref) == 40 and all(c in "0123456789abcdef" for c in ref), (
            f"Action non pinnée par SHA 40 chars : {line}"
        )


def test_github_workflow_matrix_has_two_ansible_versions():
    data = yaml.safe_load(GH_WORKFLOW.read_text())
    sanity_job = data["jobs"].get("sanity") or list(data["jobs"].values())[0]
    matrix = sanity_job.get("strategy", {}).get("matrix", {})
    ansible_versions = matrix.get("ansible", [])
    assert len(ansible_versions) >= 2, (
        f"La matrice doit contenir ≥2 versions d'ansible-core, vu : {ansible_versions}"
    )


def test_github_workflow_matrix_has_two_python_versions():
    data = yaml.safe_load(GH_WORKFLOW.read_text())
    sanity_job = data["jobs"].get("sanity") or list(data["jobs"].values())[0]
    python_versions = sanity_job.get("strategy", {}).get("matrix", {}).get("python", [])
    assert len(python_versions) >= 2, (
        f"La matrice doit contenir ≥2 versions de Python, vu : {python_versions}"
    )


def test_gitlab_ci_exists():
    assert GITLAB_CI.is_file(), f"{GITLAB_CI} absent."


def test_gitlab_ci_has_sanity_stage():
    data = yaml.safe_load(GITLAB_CI.read_text())
    stages = data.get("stages", [])
    assert "sanity" in stages, f"Stage 'sanity' absent dans .gitlab-ci.yml, vu : {stages}"


def test_gitlab_ci_runs_ansible_test():
    content = GITLAB_CI.read_text()
    assert "ansible-test" in content, (
        ".gitlab-ci.yml doit invoquer ansible-test (sanity ou units)."
    )


def test_gitlab_ci_has_matrix():
    content = GITLAB_CI.read_text()
    assert "parallel:" in content and "matrix:" in content, (
        ".gitlab-ci.yml doit utiliser parallel:matrix pour ansible-core × Python."
    )
