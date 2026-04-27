"""Tests pytest+testinfra pour le challenge assert + fail."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_marker_exists(host):
    f = host.file("/tmp/lab-assert-validated.txt")
    assert f.exists, "Le marker doit exister apres validation reussie"
    assert f.is_file
    assert f.mode == 0o644


def test_marker_contains_validation_ok(host):
    content = host.file("/tmp/lab-assert-validated.txt").content_string
    assert "Validations OK" in content


def test_marker_contains_os_info(host):
    content = host.file("/tmp/lab-assert-validated.txt").content_string
    # AlmaLinux 10.x ou similaire
    assert "AlmaLinux" in content or "Rocky" in content or "RedHat" in content
