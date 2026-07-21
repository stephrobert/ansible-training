"""Tests pytest+testinfra pour le challenge module selinux."""

import pytest

from conftest import lab_host, assert_idempotent, reboot_and_wait

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_selinux_enforcing(host):
    cmd = host.run("getenforce")
    assert cmd.rc == 0
    assert cmd.stdout.strip() == "Enforcing"


def test_httpd_network_connect_boolean_on(host):
    cmd = host.run("getsebool httpd_can_network_connect")
    assert cmd.rc == 0
    assert "--> on" in cmd.stdout, f"Boolean doit etre on, sortie : {cmd.stdout}"


def test_myapp_dir_exists(host):
    f = host.file("/var/www/myapp")
    assert f.is_directory
    assert f.mode == 0o755


def test_myapp_dir_selinux_context(host):
    """Le contexte SELinux du dossier doit inclure httpd_sys_content_t."""
    cmd = host.run("ls -dZ /var/www/myapp")
    assert cmd.rc == 0
    assert "httpd_sys_content_t" in cmd.stdout, \
        f"Contexte attendu, sortie : {cmd.stdout}"


@pytest.mark.slow
def test_selinux_survit_vraiment_au_reboot():
    """Prouve la persistance en REDÉMARRANT db1, au lieu de lire getsebool.

    `test_httpd_network_connect_boolean_on` lit l'état RUNTIME du booléen. Or
    `setsebool httpd_can_network_connect on` (sans -P) donne exactement ce même
    runtime, et le booléen retombe à off au reboot : c'est LE piège SELinux qui
    fait perdre les points à l'examen. La persistance se prouve en redémarrant.

    Le contexte de fichier (semanage fcontext + restorecon) et le mode Enforcing
    doivent eux aussi survivre : on les revérifie après le reboot.

    Marqué `slow` (redémarrage ~90 s), désélectionnable avec `pytest -m 'not slow'`.
    """
    host = reboot_and_wait(TARGET_HOST)

    assert host.check_output("getenforce") == "Enforcing", (
        "Après reboot, SELinux n'est plus en Enforcing : le mode n'a pas été "
        "rendu persistant dans /etc/selinux/config."
    )

    boolean = host.check_output("getsebool httpd_can_network_connect")
    assert boolean.split("-->")[-1].strip() == "on", (
        "Après reboot, httpd_can_network_connect est retombé à off : posé avec "
        "`setsebool` sans -P (ou sans `persistent: true`). C'est le piège SELinux "
        "qui coûte les points, et que getsebool seul ne montre pas."
    )

    contexte = host.check_output("ls -dZ /var/www/myapp")
    assert "httpd_sys_content_t" in contexte, (
        "Après reboot, le contexte de /var/www/myapp a été perdu (vu : "
        f"{contexte}). Un `chcon` ne survit pas : il faut semanage fcontext + "
        "restorecon pour que la règle soit persistante."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
