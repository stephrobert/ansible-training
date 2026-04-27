"""Tests pytest+testinfra pour le challenge module sysctl."""

import pytest

from conftest import lab_host

TARGET_HOST = "db1.lab"
SYSCTL_FILE = "/etc/sysctl.d/99-rhce-lab.conf"

PARAMS = [
    ("net.ipv4.ip_forward", "1"),
    ("net.ipv4.tcp_syncookies", "1"),
    ("kernel.kptr_restrict", "2"),
    ("vm.swappiness", "10"),
]


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_sysctl_file_exists(host):
    f = host.file(SYSCTL_FILE)
    assert f.exists
    assert f.is_file


@pytest.mark.parametrize("name,value", PARAMS)
def test_param_in_file(host, name, value):
    """Le parametre est ecrit dans le fichier dedie."""
    content = host.file(SYSCTL_FILE).content_string
    assert f"{name} = {value}" in content or f"{name}={value}" in content


@pytest.mark.parametrize("name,value", PARAMS)
def test_param_runtime_value(host, name, value):
    """La valeur effective via sysctl -n correspond."""
    cmd = host.run(f"sysctl -n {name}")
    assert cmd.rc == 0
    assert cmd.stdout.strip() == value, \
        f"{name} attendu {value}, runtime : {cmd.stdout.strip()}"
