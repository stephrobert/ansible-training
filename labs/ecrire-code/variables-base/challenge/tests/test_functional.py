"""Tests pytest+testinfra pour le challenge variables-base."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
RESULT_FILE = "/tmp/challenge-vars.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_result_file_exists(host):
    f = host.file(RESULT_FILE)
    assert f.exists, message(
        en=f"{RESULT_FILE} must have been created by solution.yml",
        fr=f"{RESULT_FILE} doit avoir été créé par solution.yml",
    )


def test_extra_vars_overrides_play_vars(host):
    """--extra-vars (niveau 22) écrase vars: du play."""
    f = host.file(RESULT_FILE)
    assert "service_name=production-api" in f.content_string, message(
        en="service_name must be 'production-api' (--extra-vars). If you see "
        "'default-service', --extra-vars was not passed.",
        fr="service_name doit valoir 'production-api' (--extra-vars). "
        "Si vous voyez 'default-service', --extra-vars n'a pas été passé.",
    )


def test_play_vars_kept_when_not_overridden(host):
    """vars: du play s'applique en l'absence d'override."""
    f = host.file(RESULT_FILE)
    assert "service_port=8000" in f.content_string, message(
        en="service_port must be 8000 (the play's vars:, with no override).",
        fr="service_port doit valoir 8000 (vars: du play, pas d'override).",
    )


def test_vars_files_loaded(host):
    """vars_files: charge bien db.yml."""
    f = host.file(RESULT_FILE)
    assert "db_engine=postgresql" in f.content_string, message(
        en="db_engine must be 'postgresql' (vars_files: vars/db.yml).",
        fr="db_engine doit valoir 'postgresql' (vars_files: vars/db.yml).",
    )


def test_extra_vars_overrides_vars_files(host):
    """--extra-vars écrase aussi vars_files:."""
    f = host.file(RESULT_FILE)
    assert "db_max_connections=500" in f.content_string, message(
        en="db_max_connections must be 500 (--extra-vars), not 100 (vars_files:).",
        fr="db_max_connections doit valoir 500 (--extra-vars), "
        "pas 100 (vars_files:).",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
