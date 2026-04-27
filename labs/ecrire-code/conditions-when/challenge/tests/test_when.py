"""Tests pytest+testinfra pour le challenge conditions-when."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_redhat_marker_exists(host):
    f = host.file("/tmp/cond-redhat.txt")
    assert f.exists, "ansible_os_family doit être RedHat sur AlmaLinux"
    assert "famille=redhat" in f.content_string


def test_alma10_marker_exists(host):
    f = host.file("/tmp/cond-alma10.txt")
    assert f.exists, "AlmaLinux 10+ doit déclencher cond-alma10"
    assert "os=AlmaLinux10" in f.content_string


def test_feature_marker_exists(host):
    """Avec --extra-vars enable_feature=true, le fichier est posé."""
    f = host.file("/tmp/cond-feature.txt")
    assert f.exists, (
        "Avec --extra-vars enable_feature=true, /tmp/cond-feature.txt "
        "doit exister."
    )
    assert "feature=enabled" in f.content_string


def test_debian_marker_does_not_exist(host):
    """Sur AlmaLinux, ansible_os_family != Debian → fichier non posé."""
    f = host.file("/tmp/cond-debian.txt")
    assert not f.exists, (
        "Sur AlmaLinux, le fichier debian ne doit PAS exister."
    )
