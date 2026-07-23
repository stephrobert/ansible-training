"""Tests pytest+testinfra pour le challenge conditions-when."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_redhat_marker_exists(host):
    f = host.file("/tmp/cond-redhat.txt")
    assert f.exists, "ansible_os_family doit être RedHat sur AlmaLinux"
    assert "famille=redhat" in f.content_string


def test_alma9_marker_exists(host):
    f = host.file("/tmp/cond-alma9.txt")
    assert f.exists, "AlmaLinux 9+ doit déclencher cond-alma9"
    assert "os=AlmaLinux9" in f.content_string


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


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
