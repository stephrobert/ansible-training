"""Tests pytest+testinfra pour le challenge module package."""

import pytest

from conftest import lab_host

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("pkg", ["vim-enhanced", "bash-completion", "tree"])
def test_package_installed(host, pkg):
    assert host.package(pkg).is_installed, f"{pkg} doit etre installe"


def test_telnet_absent(host):
    assert not host.package("telnet").is_installed


def test_vim_binary_in_path(host):
    cmd = host.run("which vim")
    assert cmd.rc == 0, "vim doit etre dans le PATH (fourni par vim-enhanced)"
