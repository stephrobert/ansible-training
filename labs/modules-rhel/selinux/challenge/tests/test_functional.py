"""Tests pytest+testinfra pour le challenge module selinux.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message, reboot_and_wait

TARGET_HOST = "db1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_selinux_enforcing(host):
    cmd = host.run("getenforce")
    assert cmd.rc == 0, message(
        en=f"getenforce does not answer: {cmd.stderr.strip()}",
        fr=f"getenforce ne répond pas : {cmd.stderr.strip()}",
    )
    assert cmd.stdout.strip() == "Enforcing", message(
        en=f"SELinux is in {cmd.stdout.strip()}, expected Enforcing. "
           f"ansible.posix.selinux with state: enforcing and "
           f"policy: targeted.",
        fr=f"SELinux est en {cmd.stdout.strip()}, attendu Enforcing. "
           f"ansible.posix.selinux avec state: enforcing et "
           f"policy: targeted.",
    )


def test_httpd_network_connect_boolean_on(host):
    cmd = host.run("getsebool httpd_can_network_connect")
    assert cmd.rc == 0, message(
        en=f"getsebool does not answer: {cmd.stderr.strip()}. The SELinux "
           f"Ansible modules need policycoreutils-python-utils.",
        fr=f"getsebool ne répond pas : {cmd.stderr.strip()}. Les modules "
           f"Ansible SELinux ont besoin de policycoreutils-python-utils.",
    )
    assert "--> on" in cmd.stdout, message(
        en=f"httpd_can_network_connect is off (output: {cmd.stdout.strip()}). "
           f"ansible.posix.seboolean with state: true, and persistent: true "
           f"so it survives a reboot.",
        fr=f"httpd_can_network_connect est à off (sortie : "
           f"{cmd.stdout.strip()}). ansible.posix.seboolean avec state: true, "
           f"et persistent: true pour qu'il survive à un redémarrage.",
    )


def test_myapp_dir_exists(host):
    f = host.file("/var/www/myapp")
    assert f.is_directory, message(
        en="/var/www/myapp is not a directory. Create it with "
           "ansible.builtin.file and state: directory before giving it a "
           "SELinux context.",
        fr="/var/www/myapp n'est pas un répertoire. Crée-le avec "
           "ansible.builtin.file et state: directory avant de lui poser un "
           "contexte SELinux.",
    )
    assert f.mode == 0o755, message(
        en=f"/var/www/myapp is {oct(f.mode)}, expected 0755.",
        fr=f"/var/www/myapp est en {oct(f.mode)}, attendu 0755.",
    )


def test_myapp_dir_selinux_context(host):
    """Le contexte SELinux du dossier doit inclure httpd_sys_content_t."""
    cmd = host.run("ls -dZ /var/www/myapp")
    assert cmd.rc == 0, message(
        en=f"ls -dZ does not answer: {cmd.stderr.strip()}",
        fr=f"ls -dZ ne répond pas : {cmd.stderr.strip()}",
    )
    assert "httpd_sys_content_t" in cmd.stdout, message(
        en=f"/var/www/myapp does not carry the httpd_sys_content_t context "
           f"(seen: {cmd.stdout.strip()}). Declare the rule with "
           f"community.general.sefcontext, then APPLY it with a restorecon: "
           f"the rule alone changes nothing on files already there.",
        fr=f"/var/www/myapp ne porte pas le contexte httpd_sys_content_t "
           f"(vu : {cmd.stdout.strip()}). Déclare la règle avec "
           f"community.general.sefcontext, puis APPLIQUE-la avec un "
           f"restorecon : la règle seule ne change rien aux fichiers déjà là.",
    )


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

    assert host.check_output("getenforce") == "Enforcing", message(
        en="After reboot, SELinux is no longer Enforcing: the mode was not "
           "made persistent in /etc/selinux/config.",
        fr="Après reboot, SELinux n'est plus en Enforcing : le mode n'a pas "
           "été rendu persistant dans /etc/selinux/config.",
    )

    boolean = host.check_output("getsebool httpd_can_network_connect")
    assert boolean.split("-->")[-1].strip() == "on", message(
        en="After reboot, httpd_can_network_connect fell back to off: it was "
           "set with setsebool without -P (or without persistent: true). "
           "This is the SELinux trap that costs exam points, and getsebool "
           "alone never shows it.",
        fr="Après reboot, httpd_can_network_connect est retombé à off : posé "
           "avec setsebool sans -P (ou sans persistent: true). C'est le piège "
           "SELinux qui coûte les points, et que getsebool seul ne montre pas.",
    )

    contexte = host.check_output("ls -dZ /var/www/myapp")
    assert "httpd_sys_content_t" in contexte, message(
        en=f"After reboot, the context of /var/www/myapp is lost (seen: "
           f"{contexte}). A chcon does not survive: semanage fcontext plus "
           f"restorecon is what makes the rule persistent.",
        fr=f"Après reboot, le contexte de /var/www/myapp a été perdu (vu : "
           f"{contexte}). Un chcon ne survit pas : il faut semanage fcontext "
           f"plus restorecon pour que la règle soit persistante.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
