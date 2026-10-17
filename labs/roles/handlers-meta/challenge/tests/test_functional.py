"""Tests pytest+testinfra pour le challenge handlers + meta.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"

JOURNAL_DEPLOIEMENT = "/var/log/webserver-deploy.log"
JOURNAL_HANDLER = "/var/log/deploy-notification.log"
PAGE = "/usr/share/nginx/html/index.html"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_running(host):
    """Le service nginx est démarré (handler Reload nginx déclenché par template)."""
    assert host.service("nginx").is_running, message(
        en="nginx is not running. The role starts it; if it fails to start, "
           "look at the port: 8080 may already be taken, or the generated "
           "configuration may be invalid.",
        fr="nginx ne tourne pas. Le rôle le démarre ; s'il refuse de démarrer, "
           "regarde du côté du port : 8080 peut être déjà pris, ou la "
           "configuration générée être invalide.",
    )


def test_deploy_log_exists(host):
    """La tâche 'Tracer le déploiement' a posé /var/log/webserver-deploy.log."""
    f = host.file(JOURNAL_DEPLOIEMENT)
    assert f.exists, message(
        en=f"{JOURNAL_DEPLOIEMENT} is missing: the role's « Tracer le "
           f"déploiement » task did not run. Check the role really is applied "
           f"on db1.lab.",
        fr=f"{JOURNAL_DEPLOIEMENT} est absent : la tâche « Tracer le "
           f"déploiement » du rôle n'a pas tourné. Vérifie que le rôle est "
           f"bien appliqué sur db1.lab.",
    )
    assert f.mode == 0o644, message(
        en=f"{JOURNAL_DEPLOIEMENT} is {oct(f.mode)}, expected 0644.",
        fr=f"{JOURNAL_DEPLOIEMENT} est en {oct(f.mode)}, attendu 0644.",
    )


def test_deploy_log_contains_hostname(host):
    """Le log de déploiement contient le hostname."""
    content = host.file(JOURNAL_DEPLOIEMENT).content_string
    assert TARGET_HOST in content, message(
        en=f"The deployment log does not mention {TARGET_HOST}. The value "
           f"comes from inventory_hostname, rendered at run time, and is not "
           f"written by hand.",
        fr=f"Le journal de déploiement ne mentionne pas {TARGET_HOST}. La "
           f"valeur vient d'inventory_hostname, rendue à l'exécution, et ne "
           f"s'écrit pas à la main.",
    )


def test_handler_notify_deployment_fired(host):
    """Le handler 'Notify deployment' a été déclenché → log existe."""
    assert host.file(JOURNAL_HANDLER).exists, message(
        en="The « Notify deployment » handler did not create its log, so it "
           "never fired. A handler only runs if a task reports changed: on a "
           "second, unchanged run, nothing notifies it.",
        fr="Le handler « Notify deployment » n'a pas créé son journal, donc il "
           "ne s'est jamais déclenché. Un handler ne tourne que si une tâche "
           "rend changed : sur un second passage sans changement, rien ne le "
           "notifie.",
    )


def test_handler_notify_log_content(host):
    """Le log du handler contient les bonnes informations."""
    content = host.file(JOURNAL_HANDLER).content_string
    assert "Deployment completed" in content, message(
        en="The handler's log does not carry « Deployment completed ».",
        fr="Le journal du handler ne porte pas « Deployment completed ».",
    )
    assert TARGET_HOST in content, message(
        en=f"The handler's log does not mention {TARGET_HOST}.",
        fr=f"Le journal du handler ne mentionne pas {TARGET_HOST}.",
    )
    assert "8080" in content, message(
        en="Port 8080 does not appear in the handler's log: the override did "
           "not reach the role. webserver_listen_port goes under vars: of the "
           "« - role: webserver » entry, which is a role param.",
        fr="Le port 8080 n'apparaît pas dans le journal du handler : la "
           "surcharge n'a pas atteint le rôle. webserver_listen_port se pose "
           "sous le vars: de l'entrée « - role: webserver », qui est un role "
           "param.",
    )


def test_index_content_override(host):
    """Override de webserver_index_content → effectif dans la page servie.

    Le défaut du rôle est '<h1>Hello from ...</h1>' ; l'énoncé impose un
    message custom incluant `inventory_hostname`. On prouve l'override sur le
    contenu réel de /usr/share/nginx/html/index.html, pas sur les logs.
    """
    f = host.file(PAGE)
    assert f.exists, message(
        en=f"{PAGE} does not exist: the role did not deploy its page.",
        fr=f"{PAGE} n'existe pas : le rôle n'a pas déposé sa page.",
    )
    content = f.content_string
    assert f"handlers fired on {TARGET_HOST}" in content, message(
        en=f"The custom message is absent from the served page: the role's "
           f"default survived. webserver_index_content must be overridden, "
           f"and carry inventory_hostname.\nSeen: {content[:200]}",
        fr=f"Le message custom est absent de la page servie : le défaut du "
           f"rôle est resté. webserver_index_content doit être surchargé, et "
           f"porter inventory_hostname.\nVu : {content[:200]}",
    )


def test_nginx_listening_8080(host):
    """nginx écoute sur 8080 (port custom du challenge)."""
    cmd = host.run("ss -tlnp | grep ':8080'")
    assert cmd.rc == 0, message(
        en="Nothing is listening on port 8080. The override reached neither "
           "the template nor the service: a change in the configuration must "
           "notify the restart handler for the new port to take effect.",
        fr="Rien n'écoute sur le port 8080. La surcharge n'a atteint ni le "
           "template ni le service : un changement de configuration doit "
           "notifier le handler de redémarrage pour que le nouveau port "
           "prenne effet.",
    )
    assert "nginx" in cmd.stdout, message(
        en=f"Port 8080 is taken by something other than nginx: "
           f"{cmd.stdout.strip()}",
        fr=f"Le port 8080 est occupé par autre chose que nginx : "
           f"{cmd.stdout.strip()}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
