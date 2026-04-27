"""Tests structurels lab 87 — pipeline CI EE (GitHub Actions + GitLab CI)."""

import yaml
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2]


def test_github_workflow_exists():
    f = LAB_DIR / ".github" / "workflows" / "build-ee.yml"
    assert f.is_file()


def test_github_workflow_pins_actions_by_sha():
    content = (LAB_DIR / ".github" / "workflows" / "build-ee.yml").read_text()
    # Toutes les actions externes doivent être pinnées par SHA (40 chars)
    import re
    uses_lines = re.findall(r"uses:\s+(\S+)", content)
    for line in uses_lines:
        # Format attendu : owner/repo@<sha 40 chars>
        if "@" in line:
            ref = line.rsplit("@", 1)[1]
            assert len(ref) == 40 and all(c in "0123456789abcdef" for c in ref), (
                f"Action non pinnée par SHA : {line}"
            )


def test_github_workflow_has_minimal_permissions():
    content = (LAB_DIR / ".github" / "workflows" / "build-ee.yml").read_text()
    assert "permissions: {}" in content, "Permissions globales doivent être {}"


def test_github_workflow_uses_persist_credentials_false():
    content = (LAB_DIR / ".github" / "workflows" / "build-ee.yml").read_text()
    assert "persist-credentials: false" in content


def test_github_workflow_runs_trivy_scan():
    content = (LAB_DIR / ".github" / "workflows" / "build-ee.yml").read_text()
    assert "trivy" in content.lower()
    assert "exit-code: '1'" in content or 'exit-code: "1"' in content


def test_github_workflow_signs_with_cosign():
    content = (LAB_DIR / ".github" / "workflows" / "build-ee.yml").read_text()
    assert "cosign" in content.lower()


def test_gitlab_ci_exists_and_has_4_stages():
    f = LAB_DIR / ".gitlab-ci.yml"
    assert f.is_file()
    data = yaml.safe_load(f.read_text())
    stages = data["stages"]
    assert "build" in stages
    assert "scan" in stages
    assert "push" in stages
    assert "sign" in stages


def test_ee_yaml_uses_v3():
    data = yaml.safe_load((LAB_DIR / "execution-environment.yml").read_text())
    assert data["version"] == 3
