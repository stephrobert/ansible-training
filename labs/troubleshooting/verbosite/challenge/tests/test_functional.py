"""Tests pytest+testinfra pour le challenge lab 89 — profile_tasks."""

import configparser
from pathlib import Path

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab89-profile.txt"
LAB_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent sur {TARGET_HOST} — solution.yml a-t-elle tourné "
        f"avec ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg ?"
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, (
        f"{RESULT_FILE} doit avoir mode 0644, vu : {oct(f.mode)}"
    )


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root", (
        f"{RESULT_FILE} doit appartenir à root, vu : {f.user}"
    )


def test_file_has_three_non_empty_lines(host):
    """Le fichier contient EXACTEMENT 3 lignes non vides (les 3 noms de tâches)."""
    content = host.file(RESULT_FILE).content_string
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) == 3, (
        f"{RESULT_FILE} doit contenir exactement 3 lignes non vides "
        f"(les 3 noms de tâches), vu : {len(lines)} ligne(s).\n"
        f"Contenu : {content[:200]}"
    )


def test_ansible_cfg_livrable_existe():
    """Le livrable central du lab : un ansible.cfg de niveau lab.

    L'étape 1 de l'énoncé demande de créer cet ansible.cfg pour activer le
    profiling. Le vérifier prouve que l'apprenant a produit le livrable, pas
    seulement le fichier de preuve : un playbook sans profile_tasks poserait
    ce dernier tout autant.
    """
    lab_cfg = LAB_ROOT / "ansible.cfg"
    assert lab_cfg.is_file(), (
        f"{lab_cfg} absent — créez l'ansible.cfg du lab (étape 1 du challenge) "
        "qui active ansible.posix.profile_tasks."
    )


def test_ansible_cfg_active_profile_tasks():
    """L'ansible.cfg du lab doit activer profile_tasks et la sortie YAML.

    C'est le cœur du sujet : sans ce callback, aucun timing par tâche n'est
    produit. On lit le livrable lui-même, pas la config effective du dépôt.

    La sortie YAML ne s'obtient plus par le callback `yaml` : ce plugin a été
    SUPPRIMÉ en ansible-core 2.19 au profit d'une option du callback `default`.

    Attention au nom : l'option se documente `result_format` (ansible-doc), mais
    sa clé INI est `callback_result_format`. Écrire `result_format = yaml` dans
    un ansible.cfg ne produit rien et ne lève rien : la sortie reste en JSON.
    C'est le piège que ce test doit attraper, et qu'il laissait passer tant
    qu'il se contentait de relire la valeur déclarée.
    """
    lab_cfg = LAB_ROOT / "ansible.cfg"
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(lab_cfg)
    enabled = parser.get("defaults", "callbacks_enabled", fallback="")
    callbacks = [c.strip() for c in enabled.split(",") if c.strip()]
    assert "ansible.posix.profile_tasks" in callbacks, (
        f"ansible.posix.profile_tasks absent de callbacks_enabled dans "
        f"{lab_cfg}. callbacks_enabled vu : {callbacks}"
    )
    assert parser.get("defaults", "callback_result_format", fallback="") == "yaml", (
        f"L'ansible.cfg du lab doit définir callback_result_format = yaml dans {lab_cfg} "
        "(le callback `yaml` n'existe plus depuis ansible-core 2.19)."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
