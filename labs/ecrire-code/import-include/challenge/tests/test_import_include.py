"""Tests pytest+testinfra pour le challenge lab 30a — import vs include."""

from pathlib import Path

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
LAB_DIR = Path(__file__).resolve().parents[2]
SOLUTION = LAB_DIR / "challenge" / "solution.yml"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_solution_uses_import_tasks():
    """Le solution.yml utilise import_tasks (FQCN)."""
    if not SOLUTION.is_file():
        pytest.skip("solution.yml absent — l'apprenant doit l'écrire")
    content = SOLUTION.read_text()
    assert "import_tasks" in content, (
        "Le solution.yml doit utiliser ansible.builtin.import_tasks"
    )


def test_solution_uses_include_tasks():
    """Le solution.yml utilise include_tasks (FQCN)."""
    if not SOLUTION.is_file():
        pytest.skip("solution.yml absent")
    content = SOLUTION.read_text()
    assert "include_tasks" in content, (
        "Le solution.yml doit utiliser ansible.builtin.include_tasks (loop NE marche pas avec import_tasks)"
    )


def test_solution_uses_loop():
    """Le solution.yml a un loop: pour la version dynamique."""
    if not SOLUTION.is_file():
        pytest.skip("solution.yml absent")
    content = SOLUTION.read_text()
    assert "loop:" in content, (
        "Le solution.yml doit contenir un loop: (sur include_tasks)"
    )


def test_import_marker_exists(host):
    """Le marker de import_tasks est déposé."""
    f = host.file("/tmp/lab30a-import.txt")
    assert f.exists, "/tmp/lab30a-import.txt absent — import_tasks a-t-il tourné ?"
    assert f.mode == 0o644
    content = f.content_string
    assert "import-static" in content or "import" in content.lower(), (
        f"Le marker import doit contenir 'import-static' ou 'import', vu : {content[:100]}"
    )


def test_loop_markers_exist(host):
    """Les 3 markers de la loop sont déposés."""
    for n in (1, 2, 3):
        f = host.file(f"/tmp/lab30a-loop-{n}.txt")
        assert f.exists, (
            f"/tmp/lab30a-loop-{n}.txt absent — la loop sur include_tasks a-t-elle tourné ?"
        )
        assert f.mode == 0o644
        content = f.content_string
        assert str(n) in content, (
            f"/tmp/lab30a-loop-{n}.txt doit contenir '{n}', vu : {content[:80]}"
        )
