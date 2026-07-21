"""Tests de la configuration Molecule enrichie par l'apprenant (lab 63).

La configuration est livrée minimale : ces tests ne passent que lorsque
l'apprenant a écrit requirements.yml, prepare.yml et les enrichissements
de molecule.yml (host_vars, test_sequence, callbacks). `molecule syntax`
est ensuite exécuté réellement pour prouver que la configuration est
acceptée par l'outil.
"""

import os
import shutil
import subprocess
from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"


def _molecule_config():
    return yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())


def test_requirements_yml_written():
    f = MOLECULE_DIR / "requirements.yml"
    assert f.exists(), (
        "molecule/default/requirements.yml manquant : déclarez les "
        "collections dont le scénario dépend"
    )
    data = yaml.safe_load(f.read_text())
    collections = data.get("collections") or []
    assert collections, "requirements.yml doit déclarer au moins une collection"
    for c in collections:
        assert isinstance(c, dict) and "version" in c, (
            "Chaque collection doit porter une contrainte de version "
            "(reproductibilité du scénario)"
        )


def test_prepare_yml_written():
    f = MOLECULE_DIR / "prepare.yml"
    assert f.exists(), (
        "molecule/default/prepare.yml manquant : écrivez le play de "
        "préparation de l'instance (prérequis hors du périmètre du rôle)"
    )
    plays = yaml.safe_load(f.read_text())
    assert isinstance(plays, list) and plays, "prepare.yml doit contenir un play"
    assert plays[0].get("tasks"), (
        "prepare.yml doit contenir au moins une tâche (paquets de diagnostic...)"
    )


def test_dependency_uses_requirements_file():
    config = _molecule_config()
    options = config.get("dependency", {}).get("options", {})
    joined = " ".join(str(v) for v in options.values())
    assert "requirements" in joined, (
        "dependency galaxy doit pointer votre requirements.yml "
        "(options.requirements-file)"
    )


def test_molecule_yml_has_inventory_host_vars():
    """host_vars surcharge les variables du rôle pour l'instance."""
    config = _molecule_config()
    host_vars = config.get("provisioner", {}).get("inventory", {}).get("host_vars", {})
    assert host_vars, (
        "provisioner.inventory.host_vars manquant : surchargez "
        "webserver_listen_port pour l'instance"
    )
    ports = [v.get("webserver_listen_port") for v in host_vars.values() if isinstance(v, dict)]
    assert 8080 in ports, (
        "webserver_listen_port doit valoir 8080 via host_vars : c'est le "
        "port que verify.yml (livré) contrôle réellement"
    )


def test_molecule_yml_has_test_sequence():
    """test_sequence personnalisée déclarée dans molecule.yml."""
    config = _molecule_config()
    seq = config.get("scenario", {}).get("test_sequence", [])
    assert seq, "Déclarez scenario.test_sequence (séquence personnalisée)"
    for step in ("prepare", "converge", "idempotence", "verify"):
        assert step in seq, (
            f"L'étape '{step}' doit figurer dans test_sequence : "
            "l'idempotence notamment est le filet de sécurité du rôle"
        )


def test_molecule_yml_has_callback_options():
    """Callbacks Ansible activés (profiling des tâches)."""
    config = _molecule_config()
    defaults = (
        config.get("provisioner", {}).get("config_options", {}).get("defaults", {})
    )
    callbacks = str(defaults.get("callback_enabled", ""))
    assert "profile_tasks" in callbacks, (
        "Activez le callback profile_tasks (temps par tâche) via "
        "provisioner.config_options.defaults.callback_enabled"
    )
    assert "timer" in callbacks, "Activez aussi le callback timer (durée totale)"


def test_molecule_syntax_passes():
    """Exécute réellement `molecule syntax` sur la configuration enrichie."""
    assert shutil.which("molecule"), (
        "molecule est introuvable sur le poste : installez-le "
        "(pipx install molecule), c'est l'outil enseigné par ce lab"
    )
    env = dict(os.environ, ANSIBLE_ROLES_PATH=str(LAB_ROOT / "roles"))
    result = subprocess.run(
        ["molecule", "syntax"],
        cwd=LAB_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"`molecule syntax` échoue sur votre configuration :\n{result.stdout}{result.stderr}"
    )
