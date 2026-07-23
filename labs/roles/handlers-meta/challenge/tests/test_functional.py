"""Tests pytest+testinfra pour le challenge handlers + meta."""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_running(host):
    """Le service nginx est démarré (handler Reload nginx déclenché par template)."""
    svc = host.service("nginx")
    assert svc.is_running


def test_deploy_log_exists(host):
    """La tâche 'Tracer le déploiement' a posé /var/log/webserver-deploy.log."""
    f = host.file("/var/log/webserver-deploy.log")
    assert f.exists
    assert f.mode == 0o644


def test_deploy_log_contains_hostname(host):
    """Le log de déploiement contient le hostname."""
    content = host.file("/var/log/webserver-deploy.log").content_string
    assert "db1.lab" in content


def test_handler_notify_deployment_fired(host):
    """Le handler 'Notify deployment' a été déclenché → log existe."""
    f = host.file("/var/log/deploy-notification.log")
    assert f.exists, "Handler 'Notify deployment' n'a pas créé son log"


def test_handler_notify_log_content(host):
    """Le log du handler contient les bonnes informations."""
    content = host.file("/var/log/deploy-notification.log").content_string
    assert "Deployment completed" in content
    assert "db1.lab" in content
    assert "8080" in content, "Port 8080 (override) doit apparaître dans le log"


def test_index_content_override(host):
    """Override de webserver_index_content → effectif dans la page servie.

    Le défaut du rôle est '<h1>Hello from ...</h1>' ; l'énoncé impose un
    message custom incluant `inventory_hostname`. On prouve l'override sur le
    contenu réel de /usr/share/nginx/html/index.html, pas sur les logs.
    """
    f = host.file("/usr/share/nginx/html/index.html")
    assert f.exists, "/usr/share/nginx/html/index.html doit exister"
    content = f.content_string
    assert "handlers fired on db1.lab" in content, (
        f"Le message custom (override webserver_index_content) est absent de "
        f"la page servie — le défaut du rôle est resté.\nContenu: {content[:200]}"
    )


def test_nginx_listening_8080(host):
    """nginx écoute sur 8080 (port custom du challenge)."""
    cmd = host.run("ss -tlnp | grep ':8080'")
    assert cmd.rc == 0
    assert "nginx" in cmd.stdout


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
