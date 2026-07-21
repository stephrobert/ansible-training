"""Tests du tox.ini écrit par l'apprenant (lab 67).

Le tox.ini est livré en squelette : ces tests parsent la configuration
(configparser, pas de grep) et ne passent que lorsqu'elle est réellement
écrite. Si tox est installé sur le poste, `tox --listenvs` est exécuté
pour prouver que la configuration est acceptée par l'outil.

Un run complet (`tox`) installerait N venvs et lancerait molecule sur
chacun : trop long pour ce harnais, il reste la validation manuelle
documentée dans le README.
"""

import configparser
import shutil
import subprocess
from pathlib import Path

import pytest

LAB_ROOT = Path(__file__).resolve().parents[2]
TOX_INI = LAB_ROOT / "tox.ini"


def _parser():
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    return parser


def test_tox_ini_present():
    assert TOX_INI.exists(), "tox.ini manquant : le squelette livré a-t-il été supprimé ?"


def test_tox_envlist_has_multiple_ansible_versions():
    parser = _parser()
    envlist = parser["tox"].get("envlist", "")
    assert "ansible" in envlist, "envlist doit cibler des environnements ansible-X"
    assert "{" in envlist, (
        "Utilisez la syntaxe range de tox (ansible-2.{X,Y,Z}) pour factoriser"
    )
    versions = [v for v in ("16", "17", "18", "19") if v in envlist]
    assert len(versions) >= 3, (
        f"Au moins 3 versions d'ansible-core dans envlist, vu : {envlist!r}"
    )


def test_testenv_runs_molecule_test():
    parser = _parser()
    assert "testenv" in parser, "Il manque la section générique [testenv]"
    cmds = parser["testenv"].get("commands", "")
    assert "molecule test" in cmds, (
        "[testenv] doit lancer `molecule test` : c'est lui qui prouve le "
        "comportement du rôle sous chaque version"
    )


def test_at_least_3_envs_per_version():
    parser = _parser()
    ansible_envs = [s for s in parser.sections() if s.startswith("testenv:ansible-")]
    assert len(ansible_envs) >= 3, (
        f"Au moins 3 sections [testenv:ansible-X] attendues, vu : {ansible_envs}"
    )


def test_each_env_pins_ansible_core():
    """Chaque env ansible-* doit épingler ansible-core, et il doit y en avoir.

    Le test était VACANT : sans aucune section `[testenv:ansible-*]`, la boucle
    n itère pas, aucune assertion ne joue, et le test est vert sur le squelette.
    """
    parser = _parser()
    envs = [s for s in parser.sections() if s.startswith("testenv:ansible-")]
    assert envs, (
        "Aucune section [testenv:ansible-*] dans tox.ini : le lab demande un "
        "environnement par version d ansible-core."
    )
    for s in envs:
        if True:
            deps = parser[s].get("deps", "")
            assert "ansible-core==" in deps, (
                f"{s} doit épingler ansible-core (ansible-core==2.X.*) dans "
                "deps : sans épinglage, tous les envs testent la même version"
            )
            assert "molecule" in deps, (
                f"{s} doit aussi installer molecule dans son venv"
            )


def test_lint_env_present():
    parser = _parser()
    assert "testenv:lint" in parser, (
        "Il manque [testenv:lint] : un env dédié lint (yamllint + "
        "ansible-lint) permet le fail-fast sans monter d'instance"
    )
    cmds = parser["testenv:lint"].get("commands", "")
    assert "ansible-lint" in cmds, "[testenv:lint] doit exécuter ansible-lint"


def test_tox_accepts_configuration():
    """Exécute réellement `tox --listenvs` sur votre configuration.

    Skip honnête si tox n'est pas installé sur le poste (pipx install tox) :
    les tests sémantiques ci-dessus restent le filet principal.
    """
    if shutil.which("tox") is None:
        pytest.skip(
            "tox absent du poste : pipx install tox pour valider ce point "
            "(la sémantique du fichier est déjà contrôlée par les autres tests)"
        )
    result = subprocess.run(
        ["tox", "--listenvs"],
        cwd=LAB_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        f"tox refuse votre configuration :\n{result.stdout}{result.stderr}"
    )
    envs = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    ansible_envs = [e for e in envs if e.startswith("ansible-")]
    assert len(ansible_envs) >= 3, (
        f"tox --listenvs doit exposer au moins 3 envs ansible-X, vu : {envs}"
    )
