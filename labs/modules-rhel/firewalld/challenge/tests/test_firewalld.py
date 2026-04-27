"""Tests pytest+testinfra pour le challenge module firewalld."""

import pytest

from conftest import lab_host

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_firewalld_running_and_enabled(host):
    svc = host.service("firewalld")
    assert svc.is_running
    assert svc.is_enabled


@pytest.mark.parametrize("service", ["http", "https"])
def test_service_enabled_runtime(host, service):
    """Service autorise en runtime."""
    cmd = host.run(f"firewall-cmd --query-service={service}")
    assert cmd.rc == 0, f"Service {service} doit etre autorise en runtime"


@pytest.mark.parametrize("service", ["http", "https"])
def test_service_enabled_permanent(host, service):
    """Service autorise en permanent."""
    cmd = host.run(f"firewall-cmd --query-service={service} --permanent")
    assert cmd.rc == 0, f"Service {service} doit etre autorise en permanent"


@pytest.mark.parametrize("port", ["8080/tcp", "8443/tcp"])
def test_port_open_runtime(host, port):
    """Port ouvert en runtime."""
    cmd = host.run(f"firewall-cmd --query-port={port}")
    assert cmd.rc == 0, f"Port {port} doit etre ouvert en runtime"


@pytest.mark.parametrize("port", ["8080/tcp", "8443/tcp"])
def test_port_open_permanent(host, port):
    """Port ouvert en permanent."""
    cmd = host.run(f"firewall-cmd --query-port={port} --permanent")
    assert cmd.rc == 0, f"Port {port} doit etre ouvert en permanent"
