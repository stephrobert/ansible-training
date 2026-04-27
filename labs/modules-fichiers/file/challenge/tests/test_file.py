"""Tests pytest+testinfra pour le challenge module file."""

import pytest

from conftest import lab_host

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Repertoire de release ===

def test_release_dir_exists(host):
    f = host.file("/opt/myapp/releases/v1.0.0")
    assert f.exists
    assert f.is_directory
    assert f.mode == 0o755
    assert f.user == "root"


# === Repertoire de logs ===

def test_logs_dir_exists(host):
    f = host.file("/opt/myapp/shared/logs")
    assert f.exists
    assert f.is_directory
    assert f.mode == 0o750
    assert f.user == "nobody"
    assert f.group == "nobody"


# === Lien symbolique current ===

def test_current_is_symlink(host):
    f = host.file("/opt/myapp/current")
    assert f.exists
    assert f.is_symlink
    assert f.linked_to == "/opt/myapp/releases/v1.0.0"


# === Suppression conf obsolete ===

def test_old_conf_absent(host):
    assert not host.file("/etc/myapp-old.conf").exists


# === Touch timestamp ===

def test_timestamp_exists(host):
    f = host.file("/var/log/myapp-init.timestamp")
    assert f.exists
    assert f.is_file
    assert f.mode == 0o644
