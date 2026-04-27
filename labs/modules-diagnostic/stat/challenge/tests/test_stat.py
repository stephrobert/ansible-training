"""Tests pytest+testinfra pour le challenge module stat."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_report_exists(host):
    f = host.file("/tmp/lab-stat-report.txt")
    assert f.exists
    assert f.is_file
    assert f.mode == 0o644


def test_report_contains_passwd(host):
    content = host.file("/tmp/lab-stat-report.txt").content_string
    assert "/etc/passwd" in content
    assert "exists: True" in content
    # Le mode peut etre 0644, 0o644 selon le rendu Jinja
    # Le checksum SHA256 fait 64 caracteres hex
    import re
    assert re.search(r"[a-f0-9]{64}", content), "checksum SHA256 attendu"


def test_report_contains_shadow_uid_0(host):
    content = host.file("/tmp/lab-stat-report.txt").content_string
    assert "/etc/shadow" in content
    assert "uid: 0" in content


def test_report_contains_sudoers(host):
    content = host.file("/tmp/lab-stat-report.txt").content_string
    assert "/etc/sudoers" in content
