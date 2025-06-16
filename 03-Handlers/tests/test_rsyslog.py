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
    m = re.search(r"inet:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", result.stdout)
    assert m, "Impossible de trouver l'IP IPv4 de server1"
    return m.group(1)

@pytest.fixture
def host():
    ip = get_server1_ip()
    return testinfra.get_host(f"ssh://admin@{ip}")

def test_rsyslog_cron_uncommented(host):
    f = host.file("/etc/rsyslog.d/50-default.conf")
    assert f.exists
    assert re.search(r"^\s*cron\.\*\s+/var/log/cron\.log", f.content_string, re.MULTILINE)

def test_rsyslog_service_running(host):
    svc = host.service("rsyslog")
    assert svc.is_running
    assert svc.is_enabled
