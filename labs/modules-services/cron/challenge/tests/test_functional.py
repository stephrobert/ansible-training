"""Tests pytest+testinfra pour le challenge module cron."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
CRON_FILE = "/etc/cron.d/lab-rhce"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_cron_file_exists(host):
    f = host.file(CRON_FILE)
    assert f.exists
    assert f.is_file


def test_mailto_env(host):
    content = host.file(CRON_FILE).content_string
    # Ansible peut entourer la valeur de guillemets : MAILTO="admin@lab.local"
    assert "MAILTO=admin@lab.local" in content or 'MAILTO="admin@lab.local"' in content


def test_backup_job_present(host):
    content = host.file(CRON_FILE).content_string
    assert "/usr/local/bin/backup.sh" in content
    # Verifie le pattern minute=0 hour=* en role root
    lines = [line for line in content.splitlines() if "/usr/local/bin/backup.sh" in line]
    assert any(line.startswith("0 * * * * root") for line in lines), \
        "Doit avoir une ligne '0 * * * * root /usr/local/bin/backup.sh'"


def test_cleanup_job_present(host):
    content = host.file(CRON_FILE).content_string
    assert "find /tmp -mtime +7 -delete" in content
    lines = [line for line in content.splitlines() if "find /tmp" in line]
    assert any(line.startswith("0 3 * * * root") for line in lines), \
        "Doit avoir une ligne '0 3 * * * root /usr/bin/find /tmp ...'"


def test_ansible_markers_present(host):
    """Ansible identifie ses jobs avec un marker #Ansible: <name>."""
    content = host.file(CRON_FILE).content_string
    assert "#Ansible: Backup horaire" in content
    assert "#Ansible: Cleanup quotidien" in content


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
