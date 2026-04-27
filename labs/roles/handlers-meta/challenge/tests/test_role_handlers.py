"""Tests pytest+testinfra pour le challenge handlers + meta."""

import pytest

from conftest import lab_host

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


def test_nginx_listening_8080(host):
    """nginx écoute sur 8080 (port custom du challenge)."""
    cmd = host.run("ss -tlnp | grep ':8080'")
    assert cmd.rc == 0
    assert "nginx" in cmd.stdout
