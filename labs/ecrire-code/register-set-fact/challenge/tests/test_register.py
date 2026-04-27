"""Tests pytest+testinfra pour le challenge register-set-fact."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/system-id.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_hostname_captured(host):
    """Le set_fact a bien capturé le hostname depuis register."""
    content = host.file(RESULT_FILE).content_string
    assert "system_id=db1:" in content, (
        f"Le fichier doit contenir 'system_id=db1:' (hostname court). "
        f"Reçu : {content!r}"
    )


def test_kernel_captured(host):
    """Le set_fact a bien capturé une signature kernel (.el10)."""
    content = host.file(RESULT_FILE).content_string
    assert ".el10" in content or ".x86_64" in content, (
        f"Le fichier doit contenir une signature kernel (.el10 ou .x86_64). "
        f"Reçu : {content!r}"
    )
