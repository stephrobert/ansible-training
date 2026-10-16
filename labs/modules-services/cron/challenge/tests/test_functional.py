"""Tests pytest+testinfra pour le challenge module cron.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
CRON_FILE = "/etc/cron.d/lab-rhce"

BACKUP = "/usr/local/bin/backup.sh"
CLEANUP = "find /tmp -mtime +7 -delete"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_cron_file_exists(host):
    f = host.file(CRON_FILE)
    assert f.exists, message(
        en=f"{CRON_FILE} is missing. Without cron_file:, the module writes "
           f"into the user's crontab instead of a dedicated file: pass "
           f"cron_file: lab-rhce on each task.",
        fr=f"{CRON_FILE} est absent. Sans cron_file:, le module écrit dans la "
           f"crontab de l'utilisateur au lieu d'un fichier dédié : passe "
           f"cron_file: lab-rhce sur chaque tâche.",
    )
    assert f.is_file, message(
        en=f"{CRON_FILE} is not an ordinary file.",
        fr=f"{CRON_FILE} n'est pas un fichier ordinaire.",
    )


def test_mailto_env(host):
    content = host.file(CRON_FILE).content_string
    # Ansible peut entourer la valeur de guillemets : MAILTO="admin@lab.local"
    assert (
        "MAILTO=admin@lab.local" in content
        or 'MAILTO="admin@lab.local"' in content
    ), message(
        en="MAILTO is not set in the file. An environment variable is not a "
           "job: it is written by ansible.builtin.cronvar, not by cron.",
        fr="MAILTO n'est pas posé dans le fichier. Une variable "
           "d'environnement n'est pas un job : elle s'écrit avec "
           "ansible.builtin.cronvar, et non avec cron.",
    )


def test_backup_job_present(host):
    content = host.file(CRON_FILE).content_string
    assert BACKUP in content, message(
        en=f"The hourly job is missing: nothing in {CRON_FILE} runs {BACKUP}.",
        fr=f"Le job horaire manque : rien dans {CRON_FILE} ne lance {BACKUP}.",
    )
    # Verifie le pattern minute=0 hour=* en role root
    lines = [line for line in content.splitlines() if BACKUP in line]
    assert any(line.startswith("0 * * * * root") for line in lines), message(
        en=f"The backup line does not read « 0 * * * * root » (seen: "
           f"{lines}). minute: \"0\" with hour left at its default * means "
           f"every hour on the hour; user: root puts the sixth field in "
           f"place, which only a cron_file carries.",
        fr=f"La ligne de sauvegarde ne commence pas par « 0 * * * * root » "
           f"(vu : {lines}). minute: \"0\" avec hour laissé à son défaut * "
           f"donne toutes les heures pile ; user: root pose le sixième champ, "
           f"que seul un cron_file porte.",
    )


def test_cleanup_job_present(host):
    content = host.file(CRON_FILE).content_string
    assert CLEANUP in content, message(
        en=f"The daily job is missing: nothing runs « {CLEANUP} ».",
        fr=f"Le job quotidien manque : rien ne lance « {CLEANUP} ».",
    )
    lines = [line for line in content.splitlines() if "find /tmp" in line]
    assert any(line.startswith("0 3 * * * root") for line in lines), message(
        en=f"The cleanup line does not read « 0 3 * * * root » (seen: "
           f"{lines}). That is minute: \"0\" and hour: \"3\".",
        fr=f"La ligne de nettoyage ne commence pas par « 0 3 * * * root » "
           f"(vu : {lines}). C'est minute: \"0\" et hour: \"3\".",
    )


def test_ansible_markers_present(host):
    """Ansible identifie ses jobs avec un marker #Ansible: <name>."""
    content = host.file(CRON_FILE).content_string
    for nom in ("Backup horaire", "Cleanup quotidien"):
        assert f"#Ansible: {nom}" in content, message(
            en=f"The « #Ansible: {nom} » marker is missing. name: is what "
               f"writes it, and it is MANDATORY with cron_file:: it is the "
               f"identifier the module uses to find its own line again, "
               f"instead of appending a duplicate at every run.",
            fr=f"Le marker « #Ansible: {nom} » manque. C'est name: qui "
               f"l'écrit, et il est OBLIGATOIRE avec cron_file: : c'est "
               f"l'identifiant qui permet au module de retrouver sa propre "
               f"ligne, au lieu d'en ajouter une copie à chaque passage.",
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
