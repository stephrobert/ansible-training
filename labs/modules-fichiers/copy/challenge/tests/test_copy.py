"""Tests pytest+testinfra pour le challenge module copy."""

import pytest

from conftest import lab_host

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Banner SSH (copy depuis fichier local) ===

def test_banner_ssh_exists(host):
    assert host.file("/etc/ssh/banner-rhce").exists


def test_banner_ssh_mode(host):
    f = host.file("/etc/ssh/banner-rhce")
    assert f.mode == 0o644
    assert f.user == "root"
    assert f.group == "root"


def test_banner_ssh_content(host):
    content = host.file("/etc/ssh/banner-rhce").content_string
    assert content.startswith("=====")
    assert "Acces autorise uniquement" in content


# === Motd (copy depuis content inline) ===

def test_motd_rhce_exists(host):
    assert host.file("/etc/motd-rhce").exists


def test_motd_rhce_mode(host):
    f = host.file("/etc/motd-rhce")
    assert f.mode == 0o644


def test_motd_rhce_content(host):
    content = host.file("/etc/motd-rhce").content_string
    assert "Serveur RHCE" in content
    assert "gere par Ansible" in content
