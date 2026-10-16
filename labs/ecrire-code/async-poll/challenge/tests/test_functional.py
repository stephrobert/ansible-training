"""Tests pytest+testinfra pour le challenge async-poll."""

import pytest

from conftest import lab_host, message

TARGET_HOST = "db1.lab"
ASYNC_FILE = "/tmp/async-done.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_async_file_exists(host):
    f = host.file(ASYNC_FILE)
    assert f.exists, message(
        en=f"{ASYNC_FILE} does not exist. The async job may have been killed by "
        f"the timeout, or async_status did not wait for it to finish.",
        fr=f"{ASYNC_FILE} n'existe pas. Le job async a peut-être été tué "
        f"par le timeout, ou async_status n'a pas attendu sa fin.",
    )


def test_async_file_content(host):
    f = host.file(ASYNC_FILE)
    assert "Async OK" in f.content_string, message(
        en=f"{ASYNC_FILE} does not contain 'Async OK'.",
        fr=f"{ASYNC_FILE} ne contient pas 'Async OK'.",
    )

# Pas de test d'idempotence ici, volontairement.
# Ce lab lance une tâche asynchrone via `shell:`, non idempotent par nature
# (son README l'assume et impose `changed_when: true`). Exiger changed=0 ici
# contredirait ce que le lab enseigne.
