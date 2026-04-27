"""Tests pytest+testinfra pour le challenge module systemd_service."""

import pytest

from conftest import lab_host

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === chronyd (NTP, evite les conflits de port avec nginx/httpd existants) ===

def test_chrony_installed(host):
    assert host.package("chrony").is_installed


def test_chronyd_running(host):
    svc = host.service("chronyd")
    assert svc.is_running
    assert svc.is_enabled


# === Custom unit file ===

def test_lab_marker_unit_file_exists(host):
    f = host.file("/etc/systemd/system/lab-marker.service")
    assert f.exists
    assert "Description=Lab Marker Service" in f.content_string


def test_lab_marker_enabled(host):
    svc = host.service("lab-marker")
    assert svc.is_enabled


def test_lab_marker_flag_exists(host):
    """Le service est de type oneshot RemainAfterExit — il a touch le fichier."""
    assert host.file("/var/run/lab-marker.flag").exists
