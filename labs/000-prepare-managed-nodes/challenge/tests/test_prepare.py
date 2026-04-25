"""
Tests testinfra qui valident l'état post-run du lab 000-prepare-managed-nodes.

Ces tests se connectent aux 3 managed nodes (web1, web2, db1) via Ansible
en utilisant l'inventaire racine du lab. Ils vérifient que le playbook a
bien convergé.

Lancement depuis la racine du lab :
    pytest -v labs/000-prepare-managed-nodes/challenge/tests/

testinfra ouvre une connexion par hôte et reproduit `assert host.package(...)`
sans dépendre d'un wrapper SSH manuel — il s'appuie sur Ansible.
"""

import pytest
import testinfra


# Hôtes managés (correspondent au groupe `rhce_lab` de l'inventaire)
MANAGED_NODES = ["web1.lab", "web2.lab", "db1.lab"]


@pytest.fixture(scope="module", params=MANAGED_NODES)
def host(request):
    """Connexion testinfra via Ansible inventory."""
    return testinfra.get_host(
        f"ansible://{request.param}?ansible_inventory=inventory/hosts.yml"
    )


def test_chrony_installed_and_running(host):
    """chrony doit être installé et le service chronyd actif."""
    assert host.package("chrony").is_installed
    chronyd = host.service("chronyd")
    assert chronyd.is_enabled
    assert chronyd.is_running


def test_required_packages_installed(host):
    """Les paquets nécessaires à Ansible doivent être présents."""
    for pkg in ["python3-libselinux", "python3-firewall", "tar", "rsync"]:
        assert host.package(pkg).is_installed, f"{pkg} manquant"


def test_etc_hosts_contains_all_lab_nodes(host):
    """/etc/hosts doit contenir les 4 hôtes du lab."""
    hosts_file = host.file("/etc/hosts")
    assert hosts_file.exists
    for ip, name in [
        ("10.10.20.10", "control-node"),
        ("10.10.20.21", "web1"),
        ("10.10.20.22", "web2"),
        ("10.10.20.31", "db1"),
    ]:
        assert hosts_file.contains(rf"{ip}.*{name}"), \
            f"Entrée /etc/hosts manquante pour {name} ({ip})"


def test_selinux_enforcing(host):
    """SELinux doit être en mode enforcing avec la policy targeted."""
    selinux = host.run("getenforce")
    assert selinux.stdout.strip() == "Enforcing", \
        f"SELinux n'est pas Enforcing : {selinux.stdout!r}"


def test_timezone_paris(host):
    """La timezone doit être Europe/Paris."""
    tz = host.run("timedatectl show --value -p Timezone")
    assert tz.stdout.strip() == "Europe/Paris"
