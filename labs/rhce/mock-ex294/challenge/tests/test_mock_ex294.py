"""Tests pytest+testinfra pour le mock RHCE EX294 (lab 100).

12 tests indépendants (un par tâche du mock).
"""

import pytest

from conftest import lab_host


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


# ─── Tâche 1 — Inventaire (vérifié indirectement) ──────────────────────────
def test_01_inventory_groups(db1, web1):
    """Tâche 1 : groupes webservers + dbservers atteignables."""
    assert db1.system_info.distribution.lower() in ("almalinux", "rocky", "rhel")
    assert web1.system_info.distribution.lower() in ("almalinux", "rocky", "rhel")


# ─── Tâche 2 — Variables (vérifié sur un fichier produit par le playbook) ──
# Le playbook doit poser /tmp/lab100-vars.txt sur web1 contenant les vars résolues.
def test_02_variables_precedence(web1):
    """Tâche 2 : group_vars + host_vars correctement résolus."""
    f = web1.file("/tmp/lab100-vars.txt")
    assert f.exists, "Le playbook doit déposer /tmp/lab100-vars.txt sur web1"
    content = f.content_string
    assert "production" in content, "app_env doit valoir 'production'"
    assert "worker_count: 4" in content or "worker_count = 4" in content


# ─── Tâche 3 — Vault ─────────────────────────────────────────────────────
def test_03_vault_decrypted(db1):
    f = db1.file("/tmp/lab100-vault-test.txt")
    assert f.exists, "/tmp/lab100-vault-test.txt absent — vars_files vault.yml KO"
    assert f.mode == 0o600, f"Mode attendu 0600, vu : {oct(f.mode)}"
    assert "Lab92Pass" in f.content_string, "db_password déchiffré attendu"


# ─── Tâche 4 — Templates et fichiers ────────────────────────────────────
def test_04_template_app_conf(db1):
    f = db1.file("/tmp/lab100-app.conf")
    assert f.exists
    assert f.mode == 0o640, f"Mode attendu 0640, vu : {oct(f.mode)}"
    assert f.user == "appuser"
    assert f.group == "appgroup"
    assert "lab100db" in f.content_string, "db_name doit apparaître"


# ─── Tâche 5 — Paquets ──────────────────────────────────────────────────
def test_05_packages_installed(db1):
    assert db1.package("httpd").is_installed
    assert db1.package("mariadb-server").is_installed
    assert db1.package("python3-libselinux").is_installed


# ─── Tâche 6 — Services ─────────────────────────────────────────────────
def test_06_services_running(web1, db1):
    assert web1.service("httpd").is_running, "httpd KO sur web1"
    assert web1.service("httpd").is_enabled
    assert db1.service("mariadb").is_running, "mariadb KO sur db1"


# ─── Tâche 7 — Utilisateurs ─────────────────────────────────────────────
def test_07_user_appuser(db1):
    user = db1.user("appuser")
    assert user.exists
    assert user.uid == 2001
    assert user.group == "appgroup"
    grp = db1.group("appgroup")
    assert grp.exists
    assert grp.gid == 2001


# ─── Tâche 8 — SELinux ──────────────────────────────────────────────────
def test_08_selinux_httpd_can_network_connect(web1):
    cmd = web1.run("getsebool httpd_can_network_connect")
    assert cmd.rc == 0
    assert "on" in cmd.stdout, f"booléen attendu 'on', vu : {cmd.stdout}"


# ─── Tâche 9 — Firewalld ────────────────────────────────────────────────
def test_09_firewall_http_https_open(web1):
    cmd = web1.run("firewall-cmd --list-services")
    assert "http" in cmd.stdout
    assert "https" in cmd.stdout


def test_09b_firewall_mysql_db1(db1):
    cmd = db1.run("firewall-cmd --list-services")
    assert "mysql" in cmd.stdout


# ─── Tâche 10 — Stockage ────────────────────────────────────────────────
def test_10_lvm_xfs_mounted(db1):
    mount = db1.mount_point("/mnt/data")
    assert mount.exists, "/mnt/data doit être monté"
    assert mount.filesystem == "xfs"


# ─── Tâche 11 — Rôle app_deploy ─────────────────────────────────────────
def test_11_role_index_html(web1, web2):
    for host in (web1, web2):
        f = host.file("/var/www/html/index.html")
        assert f.exists, f"index.html absent sur {host.system_info.hostname}"


# ─── Tâche 12 — Conditions et boucles ───────────────────────────────────
def test_12_loop_5_files_parity(db1):
    expected = {
        1: "impair",
        2: "pair",
        3: "impair",
        4: "pair",
        5: "impair",
    }
    for n, parity in expected.items():
        f = db1.file(f"/tmp/file{n}")
        assert f.exists, f"/tmp/file{n} absent"
        assert parity in f.content_string, (
            f"/tmp/file{n} doit contenir '{parity}', vu : {f.content_string[:50]}"
        )
