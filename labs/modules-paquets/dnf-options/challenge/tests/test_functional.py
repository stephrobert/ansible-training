"""Tests pytest+testinfra pour le challenge dnf options.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_epel_release_installed(host):
    assert host.package("epel-release").is_installed, message(
        en="epel-release is not installed. It comes first: the other two "
           "packages only exist in that repository, and dnf cannot find them "
           "before it is declared.",
        fr="epel-release n'est pas installé. Il vient en premier : les deux "
           "autres paquets n'existent que dans ce dépôt, et dnf ne peut pas "
           "les trouver avant qu'il soit déclaré.",
    )


@pytest.mark.parametrize("pkg", ["htop", "ncdu"])
def test_epel_packages_installed(host, pkg):
    assert host.package(pkg).is_installed, message(
        en=f"{pkg} is not installed. It comes from EPEL: install both in a "
           f"single dnf task, by passing name: a list rather than looping, "
           f"which resolves dependencies once.",
        fr=f"{pkg} n'est pas installé. Il vient d'EPEL : installe les deux en "
           f"une seule tâche dnf, en passant une liste à name: plutôt qu'une "
           f"boucle, ce qui résout les dépendances en une fois.",
    )


def test_htop_runs(host):
    cmd = host.run("htop --version")
    assert cmd.rc == 0, message(
        en=f"htop is installed but does not run: {cmd.stderr.strip()}",
        fr=f"htop est installé mais ne s'exécute pas : {cmd.stderr.strip()}",
    )


def test_epel_repo_configured(host):
    """Verifie qu un fichier .repo EPEL existe dans /etc/yum.repos.d/."""
    cmd = host.run("ls /etc/yum.repos.d/ | grep -i epel")
    assert cmd.rc == 0, message(
        en="No EPEL .repo file in /etc/yum.repos.d/: the repository is not "
           "configured, so its packages came from somewhere else.",
        fr="Aucun fichier .repo EPEL dans /etc/yum.repos.d/ : le dépôt n'est "
           "pas configuré, donc ses paquets viennent d'ailleurs.",
    )
    assert "epel" in cmd.stdout.lower(), message(
        en=f"No file matching epel found: {cmd.stdout.strip()}",
        fr=f"Aucun fichier correspondant à epel : {cmd.stdout.strip()}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
