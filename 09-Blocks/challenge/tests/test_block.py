import subprocess
import re
import pytest
import testinfra

def get_server1_ip():
    # Exécuter la commande incus info
    result = subprocess.run(
        ["incus", "info", "server1"], capture_output=True, text=True, check=True
    )
    # Rechercher l'IP IPv4 dans la sortie
    m = re.search(r"inet:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/.* \(global\)", result.stdout)
    assert m, "Impossible de trouver l'IP IPv4 de server1"
    return m.group(1)

@pytest.fixture
def host():
    ip = get_server1_ip()
    return testinfra.get_host(f"ssh://admin@{ip}")

def test_fail2ban_service_not_running_on_server1(host):
    svc = host.service("fail2ban")
    assert svc.is_running
    assert svc.is_enabled


def test_file_exists_on_server1(host):
    f = host.file("/tmp/fail2ban_status.log")
    assert f.exists
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644

def get_server2_ip():
    result = subprocess.run(
        ["incus", "info", "server2"], capture_output=True, text=True, check=True
    )
    m = re.search(r"inet:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/.* \(global\)", result.stdout)
    assert m, "Impossible de trouver l'IP IPv4 de server2"
    return m.group(1)

@pytest.fixture
def host_server2():
    ip = get_server2_ip()
    return testinfra.get_host(f"ssh://admin@{ip}")

def test_fail2ban_service_not_running_on_server2(host_server2):
    svc = host_server2.service("fail2ban")
    assert not svc.is_running

def test_file_exists_on_server2(host_server2):
    f = host_server2.file("/tmp/fail2ban_status.log")
    assert f.exists
    assert f.is_file
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
