"""Tests structure du workflow GitHub Actions (lab 69)."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = LAB_ROOT / ".github/workflows/test.yml"


def test_workflow_file_present():
    assert WORKFLOW.exists()


def test_workflow_has_lint_and_molecule_jobs():
    config = yaml.safe_load(WORKFLOW.read_text())
    jobs = config["jobs"]
    assert "lint" in jobs
    assert "molecule" in jobs


def test_lint_job_runs_ansible_lint():
    config = yaml.safe_load(WORKFLOW.read_text())
    steps = config["jobs"]["lint"]["steps"]
    cmds = " ".join(s.get("run", "") for s in steps if "run" in s)
    assert "ansible-lint" in cmds
    assert "yamllint" in cmds


def test_molecule_job_uses_matrix_strategy():
    """Matrice multi-distros + multi-versions ansible-core."""
    config = yaml.safe_load(WORKFLOW.read_text())
    matrix = config["jobs"]["molecule"]["strategy"]["matrix"]
    assert "distro" in matrix
    assert "ansible" in matrix
    assert len(matrix["distro"]) >= 2
    assert len(matrix["ansible"]) >= 2


def test_molecule_job_depends_on_lint():
    """molecule job ne tourne que si lint passe (fail-fast)."""
    config = yaml.safe_load(WORKFLOW.read_text())
    needs = config["jobs"]["molecule"]["needs"]
    assert needs == "lint" or "lint" in needs


def test_actions_pinned_by_sha():
    """Actions checkout/setup-python pinnées par SHA (sécurité)."""
    content = WORKFLOW.read_text()
    # Recherche du pattern "uses: <action>@<sha40>"
    import re
    pattern = re.compile(r'uses: [\w-]+/[\w-]+@[a-f0-9]{40}')
    matches = pattern.findall(content)
    assert len(matches) >= 2, "Au moins 2 actions doivent être pinnées par SHA"


def test_permissions_minimal():
    """permissions: {} au top + contents:read par job (least-privilege)."""
    config = yaml.safe_load(WORKFLOW.read_text())
    assert "permissions" in config
    assert config["permissions"] == {} or config["permissions"] == "{}"


def test_persist_credentials_false():
    """checkout configuré avec persist-credentials: false."""
    content = WORKFLOW.read_text()
    assert "persist-credentials: false" in content
