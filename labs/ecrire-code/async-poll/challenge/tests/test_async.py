"""Tests pytest+testinfra pour le challenge async-poll."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
ASYNC_FILE = "/tmp/async-done.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_async_file_exists(host):
    f = host.file(ASYNC_FILE)
    assert f.exists, (
        f"{ASYNC_FILE} n'existe pas. Le job async a peut-être été tué "
        f"par le timeout, ou async_status n'a pas attendu sa fin."
    )


def test_async_file_content(host):
    f = host.file(ASYNC_FILE)
    assert "Async OK" in f.content_string, (
        f"{ASYNC_FILE} ne contient pas 'Async OK'."
    )
