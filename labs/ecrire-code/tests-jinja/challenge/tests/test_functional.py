"""Tests pytest+testinfra pour le challenge tests-jinja."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/tests-jinja.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_file_exists(host):
    assert host.file(RESULT_FILE).exists


@pytest.mark.parametrize("line", [
    "user_defined=yes",
    "config_mapping=yes",
    "ports_sequence=yes",
    "optional_undefined=yes",
])
def test_lines_present(host, line):
    content = host.file(RESULT_FILE).content_string
    assert line in content


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
