"""
Tests pytest+testinfra pour le challenge "Handlers" (nginx avec deux handlers).
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
NGINX_CONF = "/etc/nginx/nginx.conf"
JOURNAL = "/var/log/ansible-handlers.log"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_running(host):
    assert host.package("nginx").is_installed, message(
        en="nginx is not installed: the role's install task did not run, so "
           "no handler could fire either.",
        fr="nginx n'est pas installé : la tâche d'installation du rôle n'a "
           "pas tourné, donc aucun handler n'a pu se déclencher non plus.",
    )
    svc = host.service("nginx")
    assert svc.is_running, message(
        en="nginx must be running",
        fr="nginx doit être running",
    )
    assert svc.is_enabled, message(
        en="nginx must be enabled at boot",
        fr="nginx doit être enabled",
    )


def test_server_tokens_off(host):
    """nginx.conf doit contenir 'server_tokens off;'."""
    f = host.file(NGINX_CONF)
    assert f.exists, message(
        en=f"{NGINX_CONF} does not exist: the package was installed but its "
           f"configuration was never deployed.",
        fr=f"{NGINX_CONF} n'existe pas : le paquet est installé mais sa "
           f"configuration n'a jamais été déposée.",
    )
    assert "server_tokens off;" in f.content_string, message(
        en=f"{NGINX_CONF} must contain 'server_tokens off;'",
        fr=f"{NGINX_CONF} doit contenir 'server_tokens off;'",
    )


def test_nosniff_header_configured(host):
    """nginx.conf doit poser l'en-tête X-Content-Type-Options: nosniff."""
    f = host.file(NGINX_CONF)
    assert "X-Content-Type-Options" in f.content_string, message(
        en=f"{NGINX_CONF} must contain an add_header X-Content-Type-Options",
        fr=f"{NGINX_CONF} doit contenir un add_header X-Content-Type-Options",
    )


def test_journal_exists_with_entry(host):
    """Le second handler 'Notifier journal local' a posé une entrée dans le journal."""
    f = host.file(JOURNAL)
    assert f.exists, message(
        en=f"{JOURNAL} does not exist: the 'Notifier journal local' handler "
        f"never fired",
        fr=f"{JOURNAL} n'existe pas : le handler 'Notifier journal local' "
        f"ne s'est pas déclenché",
    )
    assert "Config nginx modifiée" in f.content_string, message(
        en=f"{JOURNAL} does not contain the expected entry",
        fr=f"{JOURNAL} ne contient pas l'entrée attendue",
    )


def test_http_response_200(host):
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost")
    assert cmd.stdout == "200", message(
        en=f"Expected HTTP code 200, received {cmd.stdout}",
        fr=f"Code HTTP attendu 200, reçu {cmd.stdout}",
    )


def test_server_header_is_nginx_only(host):
    """Le header Server doit être 'nginx' uniquement (preuve server_tokens off).

    C'est la preuve par l'extérieur : la directive peut être dans le fichier
    sans être appliquée si le handler « Reload nginx » n'a pas tourné. Sans
    `server_tokens off;`, nginx répond « nginx/1.26.3 ».
    """
    cmd = host.run("curl -sI http://localhost")
    assert cmd.rc == 0, message(
        en=f"curl could not reach http://localhost: nginx does not answer at "
           f"all, so nothing can be said about its headers.\n{cmd.stderr}",
        fr=f"curl n'a pas pu joindre http://localhost : nginx ne répond pas "
           f"du tout, donc rien ne peut être dit de ses en-têtes.\n"
           f"{cmd.stderr}",
    )
    server_lines = [
        line for line in cmd.stdout.splitlines() if line.lower().startswith("server:")
    ]
    assert server_lines, message(
        en=f"No Server header received. Output: {cmd.stdout}",
        fr=f"Aucun header Server reçu. Sortie : {cmd.stdout}",
    )
    server_value = server_lines[0].split(":", 1)[1].strip()
    assert server_value == "nginx", message(
        en=f"The Server header must be exactly 'nginx', with no version, "
        f"received: '{server_value}'. The 'Reload nginx' handler may not "
        f"have run after server_tokens was changed.",
        fr=f"Le header Server doit être exactement 'nginx' (sans version), "
        f"reçu : '{server_value}'. Le handler 'Reload nginx' n'a peut-être "
        f"pas tourné après la modification de server_tokens.",
    )


def test_nosniff_header_served(host):
    """L'en-tête nosniff doit être RENVOYÉ, pas seulement écrit dans le fichier.

    Même logique que le header Server : la seconde tâche de durcissement n'a
    d'effet que si le handler « Reload nginx » qu'elle notifie a tourné.
    """
    cmd = host.run("curl -sI http://localhost")
    assert cmd.rc == 0, message(
        en=f"curl could not reach http://localhost: nginx does not answer at "
           f"all, so nothing can be said about its headers.\n{cmd.stderr}",
        fr=f"curl n'a pas pu joindre http://localhost : nginx ne répond pas "
           f"du tout, donc rien ne peut être dit de ses en-têtes.\n"
           f"{cmd.stderr}",
    )
    headers = cmd.stdout.lower()
    assert "x-content-type-options: nosniff" in headers, message(
        en="The HTTP response does not carry 'X-Content-Type-Options: nosniff'. "
        "Is the directive really inside the http block, and did the "
        f"'Reload nginx' handler run?\nHeaders received:\n{cmd.stdout}",
        fr="La réponse HTTP ne porte pas 'X-Content-Type-Options: nosniff'. "
        "La directive est-elle bien dans le bloc http, et le handler "
        f"'Reload nginx' a-t-il tourné ?\nEn-têtes reçus :\n{cmd.stdout}",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
