"""Tests pytest+testinfra pour le challenge yum_repository (EPEL)."""

import pytest

from conftest import lab_host

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
