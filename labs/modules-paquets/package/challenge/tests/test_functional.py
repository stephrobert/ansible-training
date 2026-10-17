"""Tests pytest+testinfra pour le challenge module package."""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("pkg", ["vim-enhanced", "bash-completion", "tree"])
def test_package_installed(host, pkg):
    assert host.package(pkg).is_installed, message(
        en=f"{pkg} must be installed",
        fr=f"{pkg} doit etre installe",
    )


def test_telnet_absent(host):
    assert not host.package("telnet").is_installed, message(
        en="telnet is still installed: state: absent removes a package, and "
           "does not fail when it was not there in the first place.",
        fr="telnet est encore installé : state: absent retire un paquet, et "
           "ne lève pas s'il n'y était pas.",
    )


def test_vim_binary_in_path(host):
    cmd = host.run("which vim")
    assert cmd.rc == 0, message(
        en="vim must be in the PATH (provided by vim-enhanced)",
        fr="vim doit etre dans le PATH (fourni par vim-enhanced)",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
