"""Tests pytest+testinfra pour le challenge dnf options."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_epel_release_installed(host):
    assert host.package("epel-release").is_installed


@pytest.mark.parametrize("pkg", ["htop", "ncdu"])
def test_epel_packages_installed(host, pkg):
    assert host.package(pkg).is_installed, f"{pkg} doit etre installe via EPEL"


def test_htop_runs(host):
    cmd = host.run("htop --version")
    assert cmd.rc == 0


def test_epel_repo_configured(host):
    """Verifie qu un fichier .repo EPEL existe dans /etc/yum.repos.d/."""
    cmd = host.run("ls /etc/yum.repos.d/ | grep -i epel")
    assert cmd.rc == 0
    assert "epel" in cmd.stdout.lower()


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
