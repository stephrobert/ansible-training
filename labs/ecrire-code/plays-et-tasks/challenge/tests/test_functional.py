"""
Tests pytest+testinfra pour le challenge "Plays et tasks" (nginx sur db1.lab).

Valide la solution écrite par l'apprenant dans
labs/ecrire-code/plays-et-tasks/challenge/solution.yml

Lancement (depuis la racine du repo) :
    pytest -v labs/ecrire-code/plays-et-tasks/challenge/tests/
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
EXPECTED_CONTENT = "Challenge OK from db1.lab"
PREDEPLOY_FILE = "/tmp/challenge-predeploy-db1.txt"
POSTDEPLOY_FILE = "/tmp/challenge-postdeploy-db1.txt"


@pytest.fixture(scope="module")
def host():
    """Connexion testinfra à db1.lab via SSH direct (cf. conftest.py racine)."""
    return lab_host(TARGET_HOST)


def test_predeploy_marker_exists(host):
    """Le fichier marqueur pre_tasks doit exister et contenir le hostname."""
    f = host.file(PREDEPLOY_FILE)
    assert f.exists, message(
        en=f"The {PREDEPLOY_FILE} file does not exist (pre_tasks did not run).",
        fr=f"Le fichier {PREDEPLOY_FILE} n'existe pas (pre_tasks pas exécuté).",
    )
    assert "db1" in f.content_string, message(
        en=f"{PREDEPLOY_FILE} does not contain the hostname (the pre_tasks must "
        f"interpolate {{ inventory_hostname }}).",
        fr=f"{PREDEPLOY_FILE} ne contient pas le hostname (le pre_tasks "
        f"doit interpoler {{ inventory_hostname }}).",
    )


def test_nginx_package_installed(host):
    """Le paquet nginx doit être installé."""
    assert host.package("nginx").is_installed, message(
        en="nginx is not installed",
        fr="nginx n'est pas installé",
    )


def test_nginx_running_and_enabled(host):
    """Le service nginx doit être actif et enabled au boot."""
    svc = host.service("nginx")
    assert svc.is_running, message(
        en="nginx is not started",
        fr="nginx n'est pas démarré",
    )
    assert svc.is_enabled, message(
        en="nginx is not enabled at boot",
        fr="nginx n'est pas enabled au boot",
    )


def test_port_80_listening(host):
    """Le port 80 doit être en listening."""
    sockets = host.socket.get_listening_sockets()
    assert any(":80" in s for s in sockets), message(
        en=f"No service listens on port 80. Sockets: {sockets}",
        fr=f"Aucun service n'écoute sur le port 80. Sockets : {sockets}",
    )


def test_firewalld_http_open(host):
    """Le service http doit être autorisé dans firewalld."""
    cmd = host.run("firewall-cmd --list-services --zone=public")
    assert cmd.rc == 0, message(
        en=f"firewall-cmd failed: {cmd.stderr}",
        fr=f"firewall-cmd échec : {cmd.stderr}",
    )
    assert "http" in cmd.stdout, message(
        en=f"The http service is not open in firewalld. "
        f"Services listed: {cmd.stdout.strip()}",
        fr=f"Le service http n'est pas ouvert dans firewalld. "
        f"Services listés : {cmd.stdout.strip()}",
    )


def test_http_response_200_with_expected_content(host):
    """curl http://localhost retourne 200 avec le contenu attendu."""
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost")
    assert cmd.stdout == "200", message(
        en=f"Expected HTTP code 200, received: {cmd.stdout}",
        fr=f"Code HTTP attendu 200, reçu : {cmd.stdout}",
    )

    cmd_content = host.run("curl -s http://localhost")
    assert EXPECTED_CONTENT in cmd_content.stdout, message(
        en=f"The page's content does not contain '{EXPECTED_CONTENT}'. "
        f"Received: {cmd_content.stdout[:300]}",
        fr=f"Le contenu de la page ne contient pas '{EXPECTED_CONTENT}'. "
        f"Reçu : {cmd_content.stdout[:300]}",
    )


def test_postdeploy_marker_exists(host):
    """Le fichier marqueur post_tasks doit exister et contenir le hostname."""
    f = host.file(POSTDEPLOY_FILE)
    assert f.exists, message(
        en=f"The {POSTDEPLOY_FILE} file does not exist (post_tasks did not run).",
        fr=f"Le fichier {POSTDEPLOY_FILE} n'existe pas (post_tasks pas exécuté).",
    )
    assert "db1" in f.content_string, message(
        en=f"{POSTDEPLOY_FILE} does not contain the hostname (the post_tasks must "
        f"interpolate {{ inventory_hostname }}).",
        fr=f"{POSTDEPLOY_FILE} ne contient pas le hostname (le post_tasks "
        f"doit interpoler {{ inventory_hostname }}).",
    )


def test_predeploy_before_postdeploy(host):
    """L'ordre pre_tasks → post_tasks doit être respecté (mtime croissant)."""
    pre = host.file(PREDEPLOY_FILE)
    post = host.file(POSTDEPLOY_FILE)
    assert pre.mtime < post.mtime, message(
        en=f"The predeploy file ({pre.mtime}) must be older than the postdeploy "
        f"file ({post.mtime}). pre_tasks must run BEFORE post_tasks.",
        fr=f"Le fichier predeploy ({pre.mtime}) doit être antérieur "
        f"au fichier postdeploy ({post.mtime}). pre_tasks doit s'exécuter "
        f"AVANT post_tasks.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
