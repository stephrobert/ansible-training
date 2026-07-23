"""Tests pytest+testinfra pour le challenge rôle nginx-server."""

import pytest

from conftest import lab_host, assert_idempotent, lab_playbook, lab_solution_text

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_package_installed(host):
    """Le paquet nginx est installé."""
    assert host.package("nginx").is_installed


def test_nginx_service_running(host):
    """Le service nginx est démarré et activé au boot."""
    svc = host.service("nginx")
    assert svc.is_running, "nginx doit être running"
    assert svc.is_enabled, "nginx doit être enabled (démarrage auto)"


def test_port_80_listening(host):
    """Le port 80 est en listening."""
    assert host.socket("tcp://0.0.0.0:80").is_listening or host.socket("tcp://:::80").is_listening


def test_firewalld_http_open(host):
    """Le service HTTP est ouvert dans firewalld zone publique."""
    cmd = host.run("firewall-cmd --zone=public --query-service=http")
    assert cmd.rc == 0, f"firewalld http non ouvert: {cmd.stdout} {cmd.stderr}"


def test_http_returns_200(host):
    """Une requête HTTP locale retourne 200."""
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost/")
    assert cmd.stdout.strip() == "200", f"Code HTTP attendu 200, reçu: {cmd.stdout}"


def test_state_comes_from_a_role():
    """Le cœur du lab : l'état nginx doit venir d'un RÔLE, pas d'un playbook plat.

    Les tests d'état système ci-dessus (paquet, service, port 80, HTTP 200)
    passeraient avec un simple playbook de tâches. Or ce lab s'appelle « créer
    ton premier rôle » : on vérifie donc qu'un rôle `nginx-server` existe avec
    sa structure standard, et que le playbook l'invoque au lieu de dérouler les
    tâches à plat.
    """
    playbook, _ = lab_playbook(__file__)
    role_dir = playbook.parent / "roles" / "nginx-server"
    for sub in ("tasks/main.yml", "defaults/main.yml", "handlers/main.yml", "meta/main.yml"):
        assert (role_dir / sub).is_file(), (
            f"Le rôle nginx-server doit contenir {sub} (structure standard d'un "
            f"rôle Ansible). Cherché dans {role_dir}."
        )

    text = lab_solution_text(__file__)
    assert "nginx-server" in text, (
        "Le playbook doit invoquer le rôle nginx-server, pas dérouler les tâches "
        "à plat."
    )
    assert "role" in text, (
        "Le playbook doit passer par un rôle (roles: / import_role / include_role)."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
