"""Tests pytest+testinfra pour le challenge inventaire dynamique KVM."""

import pytest

from conftest import lab_host

EXPECTED_HOSTS = ["control-node.lab", "web1.lab", "web2.lab", "db1.lab"]
# Mapping nom plugin libvirt → nom DNS pour testinfra
LIBVIRT_TO_DNS = {
    "control-node": "control-node.lab",
    "web1": "web1.lab",
    "web2": "web2.lab",
    "db1": "db1.lab",
}


@pytest.fixture(scope="module", params=list(LIBVIRT_TO_DNS.items()))
def vm(request):
    """Fixture paramétrique : retourne (libvirt_name, host_testinfra)."""
    libvirt_name, dns_name = request.param
    return libvirt_name, lab_host(dns_name)


def test_marker_exists(vm):
    """Le marqueur existe sur chaque VM running du lab."""
    libvirt_name, host = vm
    marker = f"/tmp/lab57-mark-{libvirt_name}.txt"
    f = host.file(marker)
    assert f.exists, f"Marqueur manquant sur {libvirt_name}: {marker}"
    assert f.mode == 0o644


def test_marker_content(vm):
    """Le contenu du marqueur prouve que l'inventaire dynamique a bien identifié la VM."""
    libvirt_name, host = vm
    marker = f"/tmp/lab57-mark-{libvirt_name}.txt"
    content = host.file(marker).content_string
    assert libvirt_name in content
    assert "running" in content
    assert "inventaire dynamique libvirt OK" in content
