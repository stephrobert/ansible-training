import subprocess
import re
import pytest
import testinfra

def get_server1_ip():
    # Exécuter la commande incus info
    result = subprocess.run(
        ["incus", "info", "myhost"], capture_output=True, text=True, check=True
    )
    # Rechercher l'IP IPv4 dans la sortie
    m = re.search(r"inet:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", result.stdout)
    assert m, "Impossible de trouver l'IP IPv4 de server1"
    return m.group(1)

@pytest.fixture
def host():
    ip = get_server1_ip()
    return testinfra.get_host(f"ssh://admin@{ip}")

def test_file_exists(host):
    assert host.file("/tmp/flag_condition.txt").exists, "Le fichier /tmp/flag_condition.txt n'existe pas"

def test_distribution(host):
    assert host.system_info.distribution == "ubuntu", "La distribution n'est pas Ubuntu"
    assert host.system_info.release.startswith("24.04"), "La version n'est pas 24.04"

def test_group_exists(host):
    assert host.group("developers").exists, "Le groupe 'developers' n'existe pas"