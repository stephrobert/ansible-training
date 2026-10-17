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
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import message

LAB_ROOT = Path(__file__).resolve().parents[2]
TOX_INI = LAB_ROOT / "tox.ini"


def _parser():
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    return parser


# Le nom d'environnement s'écrit « ansible2.19 », SANS tiret entre « ansible »
# et la version : avec un tiret, tox 4 lit « 2.19 » comme une spec
# d'interpréteur et refuse de démarrer (« could not find python interpreter
# matching any of the specs 2.19 »). Ces tests acceptent donc les deux formes
# plutôt que d'imposer celle qui ne démarre plus.
ANSIBLE_ENV = re.compile(r"^ansible-?\d")


def _ansible_env_sections(parser):
    """Sections [testenv:ansibleX] du tox.ini, quelle que soit la graphie."""
    return [
        s for s in parser.sections()
        if s.startswith("testenv:") and ANSIBLE_ENV.match(s.split(":", 1)[1])
    ]


def test_tox_ini_present():
    assert TOX_INI.exists(), message(
        en="tox.ini missing: was the provided skeleton deleted?",
        fr="tox.ini manquant : le squelette livré a-t-il été supprimé ?",
    )


def test_tox_envlist_has_multiple_ansible_versions():
    parser = _parser()
    envlist = parser["tox"].get("envlist", "")
    assert "ansible" in envlist, message(
        en="envlist must target ansibleX environments",
        fr="envlist doit cibler des environnements ansibleX",
    )
    assert "{" in envlist, message(
        en="Use tox's generative syntax (ansible2.{X,Y,Z}) to factorise",
        fr="Utilisez la syntaxe générative de tox (ansible2.{X,Y,Z}) pour factoriser",
    )
    # On compte ce que l'accolade développe réellement, au lieu de chercher une
    # liste de versions figée dans le test : celle-ci périmait le lab à chaque
    # sortie d'ansible-core, et c'est ce qui l'a mis au rouge au passage en 2.19.
    versions = [
        v
        for group in re.findall(r"\{([^}]*)\}", envlist)
        for v in group.split(",")
        if v.strip()
    ]
    assert len(versions) >= 3, message(
        en=f"At least 3 ansible-core versions in envlist, seen: {envlist!r}",
        fr=f"Au moins 3 versions d'ansible-core dans envlist, vu : {envlist!r}",
    )


def test_testenv_runs_molecule_test():
    parser = _parser()
    assert "testenv" in parser, message(
        en="The generic [testenv] section is missing",
        fr="Il manque la section générique [testenv]",
    )
    cmds = parser["testenv"].get("commands", "")
    assert "molecule test" in cmds, message(
        en="[testenv] must run `molecule test`: it is what proves the role's "
        "behaviour under each version",
        fr="[testenv] doit lancer `molecule test` : c'est lui qui prouve le "
        "comportement du rôle sous chaque version",
    )


def test_at_least_3_envs_per_version():
    parser = _parser()
    ansible_envs = _ansible_env_sections(parser)
    assert len(ansible_envs) >= 3, message(
        en=f"At least 3 [testenv:ansibleX] sections expected, seen: {ansible_envs}",
        fr=f"Au moins 3 sections [testenv:ansibleX] attendues, vu : {ansible_envs}",
    )


def test_each_env_pins_ansible_core():
    """Chaque env ansible-* doit épingler ansible-core, et il doit y en avoir.

    Le test était VACANT : sans aucune section `[testenv:ansible-*]`, la boucle
    n itère pas, aucune assertion ne joue, et le test est vert sur le squelette.
    """
    parser = _parser()
    envs = _ansible_env_sections(parser)
    assert envs, message(
        en="No [testenv:ansible*] section in tox.ini: the lab asks for one "
        "environment per ansible-core version.",
        fr="Aucune section [testenv:ansible*] dans tox.ini : le lab demande un "
        "environnement par version d ansible-core.",
    )
    for s in envs:
        if True:
            deps = parser[s].get("deps", "")
            assert "ansible-core==" in deps, message(
                en=f"{s} must pin ansible-core (ansible-core==2.X.*) in deps: without "
                "pinning, every env tests the same version",
                fr=f"{s} doit épingler ansible-core (ansible-core==2.X.*) dans "
                "deps : sans épinglage, tous les envs testent la même version",
            )
            assert "molecule" in deps, message(
                en=f"{s} must also install molecule in its venv",
                fr=f"{s} doit aussi installer molecule dans son venv",
            )


def test_lint_env_present():
    parser = _parser()
    assert "testenv:lint" in parser, message(
        en="[testenv:lint] is missing: a dedicated lint env (yamllint + "
        "ansible-lint) allows failing fast without bringing up an instance",
        fr="Il manque [testenv:lint] : un env dédié lint (yamllint + "
        "ansible-lint) permet le fail-fast sans monter d'instance",
    )
    cmds = parser["testenv:lint"].get("commands", "")
    assert "ansible-lint" in cmds, message(
        en="[testenv:lint] must run ansible-lint",
        fr="[testenv:lint] doit exécuter ansible-lint",
    )


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
    assert result.returncode == 0, message(
        en=f"tox refuses your configuration:\n{result.stdout}{result.stderr}",
        fr=f"tox refuse votre configuration :\n{result.stdout}{result.stderr}",
    )
    envs = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    ansible_envs = [e for e in envs if ANSIBLE_ENV.match(e)]
    assert len(ansible_envs) >= 3, message(
        en=f"tox --listenvs must expose at least 3 ansibleX envs, seen: {envs}",
        fr=f"tox --listenvs doit exposer au moins 3 envs ansibleX, vu : {envs}",
    )
