import subprocess
import re
import pytest
import testinfra

# Phase 2
def get_webserver1_ip():
    # Exécuter la commande incus info
    result = subprocess.run(
        ["incus", "info", "webserver1"], capture_output=True, text=True, check=True
    )
    # Rechercher l'IP IPv4 dans la sortie
    m = re.search(r"inet:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/.* \(global\)", result.stdout)
    assert m, "Impossible de trouver l'IP IPv4 de webserver1"
    return m.group(1)

@pytest.fixture
def host():
    ip = get_webserver1_ip()
    return testinfra.get_host(f"ssh://admin@{ip}")

def test_remote_directory_exists(host):
    d = host.file("/var/www/monsite")
    assert d.exists, "Le dossier /var/www/monsite est manquant"
    assert d.is_directory, "/var/www/monsite n'est pas un dossier"

def test_remote_directory_permissions_and_owner(host):
    f = host.file("/var/www/monsite")
    assert f.user == 'www-data'
    assert f.group == 'www-data'
    assert f.mode == 0o755

def test_remote_file_exists(host):
    f = host.file("/var/www/monsite/index.html")
    assert f.exists, "Le fichier /var/www/monsite/index.html n'existe pas"
    assert f.is_file, "/var/www/monsite/index.html n'est pas un fichier"

def test_remote_file_permissions_and_owner(host):
    f = host.file("/var/www/monsite/index.html")
    assert f.user == 'root'
    assert f.group == 'root'
    assert f.mode == 0o644
