"""Tests pytest+testinfra pour le challenge types-collections (selectattr)."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/services-production.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_result_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_contains_api(host):
    assert "api:8080" in host.file(RESULT_FILE).content_string


def test_contains_cache(host):
    assert "cache:6379" in host.file(RESULT_FILE).content_string


def test_excludes_staging(host):
    """Les services tier=staging ne doivent PAS apparaître."""
    content = host.file(RESULT_FILE).content_string
    assert "web:80" not in content, (
        "web (tier=staging) ne doit pas apparaître dans le fichier production."
    )


def test_excludes_dev(host):
    """Les services tier=dev ne doivent PAS apparaître."""
    content = host.file(RESULT_FILE).content_string
    assert "dev-db:5432" not in content, (
        "dev-db (tier=dev) ne doit pas apparaître dans le fichier production."
    )
