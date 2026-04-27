"""Tests pytest+testinfra pour le challenge filtres-jinja-avances."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/filtres-avances.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


def test_regex_search(host):
    """regex_search('^([a-z]+)') retourne 'web'."""
    content = host.file(RESULT_FILE).content_string
    assert "prefix=web" in content


def test_b64encode(host):
    """b64encode('admin:secret') = 'YWRtaW46c2VjcmV0'."""
    content = host.file(RESULT_FILE).content_string
    assert "b64=YWRtaW46c2VjcmV0" in content


def test_flatten(host):
    """flatten([[1,2], [3, [4,5]]]) = [1, 2, 3, 4, 5]."""
    content = host.file(RESULT_FILE).content_string
    assert "flat=[1, 2, 3, 4, 5]" in content


def test_sha256(host):
    """hash('sha256') sur 'foobar' = c3ab8ff13720..."""
    content = host.file(RESULT_FILE).content_string
    # SHA256 de 'foobar' = c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2
    assert "sha256=c3ab8ff13720" in content
