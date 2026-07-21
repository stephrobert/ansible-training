"""Tests pytest+testinfra pour le challenge lab 30a — import vs include."""

import pytest

from conftest import lab_host, lab_solution_text, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# Ces trois tests inspectent le SOURCE de la solution : ils passent par
# lab_solution_text, qui déchiffre la référence du formateur. Lire le fichier
# directement ne donnerait que du $ANSIBLE_VAULT, sans un seul import_tasks.


def test_solution_uses_import_tasks():
    """Le solution.yml utilise import_tasks (FQCN)."""
    content = lab_solution_text(__file__)
    assert "import_tasks" in content, (
        "Le solution.yml doit utiliser ansible.builtin.import_tasks"
    )


def test_solution_uses_include_tasks():
    """Le solution.yml utilise include_tasks (FQCN)."""
    content = lab_solution_text(__file__)
    assert "include_tasks" in content, (
        "Le solution.yml doit utiliser ansible.builtin.include_tasks (loop NE marche pas avec import_tasks)"
    )


def test_solution_uses_loop():
    """Le solution.yml a un loop: pour la version dynamique."""
    content = lab_solution_text(__file__)
    assert "loop:" in content, (
        "Le solution.yml doit contenir un loop: (sur include_tasks)"
    )


def test_import_marker_exists(host):
    """Le marker de import_tasks est déposé."""
    f = host.file("/tmp/lab30a-import.txt")
    assert f.exists, "/tmp/lab30a-import.txt absent — import_tasks a-t-il tourné ?"
    assert f.mode == 0o644
    assert f.user == "root", (
        f"Le fichier produit doit appartenir à root (owner: root), vu : {f.user}"
    )
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


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
