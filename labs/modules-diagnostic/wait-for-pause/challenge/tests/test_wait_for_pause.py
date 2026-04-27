"""Tests pytest+testinfra pour le challenge wait_for + pause."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_marker_file_exists(host):
    """Le fichier cree par la commande en arriere-plan (apres 3s) doit exister."""
    f = host.file("/tmp/lab-waitfor-marker.txt")
    assert f.exists


def test_success_file_exists(host):
    """Le fichier de succes ecrit apres validation des conditions."""
    f = host.file("/tmp/lab-waitfor-success.txt")
    assert f.exists
    assert f.mode == 0o644


def test_success_content(host):
    content = host.file("/tmp/lab-waitfor-success.txt").content_string
    assert "Synchronisation OK" in content


def test_sshd_listening(host):
    """sshd doit ecouter sur 22/TCP (pre-requis Ansible)."""
    cmd = host.run("ss -tln | grep ':22 '")
    assert cmd.rc == 0, "sshd doit ecouter sur 22/TCP"
