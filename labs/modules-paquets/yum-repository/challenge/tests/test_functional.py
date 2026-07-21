"""Tests pytest+testinfra pour le challenge yum_repository (EPEL)."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_epel_repo_file_existe(host):
    assert host.file("/etc/yum.repos.d/epel.repo").exists, (
        "/etc/yum.repos.d/epel.repo doit avoir été créé par yum_repository."
    )


def test_epel_enabled(host):
    """Le dépôt epel doit être enabled=1."""
    content = host.file("/etc/yum.repos.d/epel.repo").content_string
    assert "enabled = 1" in content or "enabled=1" in content, (
        f"Dépôt EPEL doit être enabled=1. Contenu : {content[:300]}"
    )


def test_htop_installed(host):
    """Paquet htop installé depuis EPEL."""
    pkg = host.package("htop")
    assert pkg.is_installed, "Paquet htop doit être installé (depuis EPEL)."


def test_epel_gpgcheck_active(host):
    """EPEL doit imposer la vérification GPG : gpgcheck actif + clé déclarée.

    C'est le point sécurité du module : un dépôt sans gpgcheck installe des RPM
    non signés. yum_repository écrit gpgcheck=1 et la gpgkey dans le .repo. Sans
    cette assertion, un apprenant qui pose gpgcheck: false passe le lab tout en
    désactivant exactement ce que l'énoncé exige.
    """
    content = host.file("/etc/yum.repos.d/epel.repo").content_string
    assert "gpgcheck = 1" in content or "gpgcheck=1" in content, (
        f"epel.repo doit avoir gpgcheck=1 (vérification GPG obligatoire). "
        f"Contenu : {content[:300]}"
    )
    assert "gpgkey" in content and "RPM-GPG-KEY-EPEL" in content, (
        "epel.repo doit déclarer la gpgkey EPEL (RPM-GPG-KEY-EPEL-*) : "
        "sans clé, gpgcheck n'a rien pour vérifier les signatures."
    )


def test_local_test_repo_file_existe(host):
    assert host.file("/etc/yum.repos.d/local-test.repo").exists, (
        "/etc/yum.repos.d/local-test.repo doit avoir été créé."
    )


def test_local_test_repo_disabled(host):
    """Le dépôt local-test doit être enabled=0 (déclaré mais désactivé)."""
    content = host.file("/etc/yum.repos.d/local-test.repo").content_string
    assert "enabled = 0" in content or "enabled=0" in content, (
        f"Dépôt local-test doit être enabled=0. Contenu : {content[:300]}"
    )


def test_local_test_repo_baseurl_local(host):
    """local-test doit pointer sur le dépôt local file:///srv/repo/.

    L'énoncé impose ce baseurl ; sans l'asserter, n'importe quelle URL passe.
    """
    content = host.file("/etc/yum.repos.d/local-test.repo").content_string
    assert "file:///srv/repo/" in content, (
        f"local-test.repo doit avoir baseurl=file:///srv/repo/. "
        f"Contenu : {content[:300]}"
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
