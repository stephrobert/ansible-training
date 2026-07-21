"""Tests pytest+testinfra pour le challenge module firewalld."""

import pytest

from conftest import lab_host, assert_idempotent, reboot_and_wait

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


@pytest.mark.slow
def test_regles_reviennent_vraiment_apres_reboot():
    """Prouve la persistance en REDÉMARRANT web1, au lieu de lire --permanent.

    Le lab fait de la persistance sa promesse centrale : « toutes les règles
    doivent être permanentes ET actives ». Les tests `..._permanent` vérifient
    que la config permanente contient les règles : c'est un indice. La preuve,
    c'est qu'après un reboot elles soient dans le RUNTIME, car c'est le runtime
    qui protège la machine. `firewall-cmd --add-service=http` sans --permanent
    passe le test runtime AVANT reboot et disparaît APRÈS : ce test l'attrape.

    Marqué `slow` (redémarrage ~90 s), désélectionnable avec `pytest -m 'not slow'`.
    """
    host = reboot_and_wait(TARGET_HOST)

    assert host.service("firewalld").is_running, (
        "Après reboot, firewalld ne tourne pas : il n'était pas activé au boot "
        "(`enabled: true`), et plus aucune règle ne protège la machine."
    )
    actifs_services = host.check_output("firewall-cmd --list-services").split()
    for svc in ("http", "https"):
        assert svc in actifs_services, (
            f"Après reboot, le service {svc} n'est plus ouvert dans le RUNTIME "
            f"(services actifs : {actifs_services}). La règle n'était pas "
            "permanente : elle a disparu au redémarrage."
        )
    actifs_ports = host.check_output("firewall-cmd --list-ports").split()
    for port in ("8080/tcp", "8443/tcp"):
        assert port in actifs_ports, (
            f"Après reboot, le port {port} n'est plus ouvert (ports actifs : "
            f"{actifs_ports}). Ajouté au runtime sans --permanent, il est perdu."
        )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
