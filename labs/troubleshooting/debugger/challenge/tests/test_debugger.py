"""Tests pytest+testinfra pour le challenge lab 90 — débogueur interactif."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/lab90-debug.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, (
        f"{RESULT_FILE} absent — solution.yml doit définir vars: target_dir=/tmp "
        f"et déposer le fichier preuve."
    )


def test_file_mode_0644(host):
    f = host.file(RESULT_FILE)
    assert f.mode == 0o644, (
        f"{RESULT_FILE} doit avoir mode 0644, vu : {oct(f.mode)}"
    )


def test_file_owned_by_root(host):
    f = host.file(RESULT_FILE)
    assert f.user == "root", f"{RESULT_FILE} doit appartenir à root, vu : {f.user}"


def test_file_contains_marker(host):
    """Le fichier contient la marque attendue après le fix."""
    content = host.file(RESULT_FILE).content_string
    assert "Debugger fix" in content or "lab 90" in content.lower(), (
        f"{RESULT_FILE} doit contenir 'Debugger fix' ou 'lab 90', "
        f"vu : {content[:200]}"
    )
