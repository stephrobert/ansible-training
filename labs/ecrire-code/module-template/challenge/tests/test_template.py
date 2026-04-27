"""Tests pytest+testinfra pour le challenge module-template."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/etc/banner.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists


def test_motd_text(host):
    content = host.file(RESULT_FILE).content_string
    assert "Bienvenue !" in content


def test_generated_metadata(host):
    content = host.file(RESULT_FILE).content_string
    assert "Generated: 2026-04-25" in content


def test_owner_metadata(host):
    content = host.file(RESULT_FILE).content_string
    assert "Owner: ops-team" in content


def test_file_mode(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644
