"""Tests structure config tox (lab 67)."""

import configparser
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
TOX_INI = LAB_ROOT / "tox.ini"


def test_tox_ini_present():
    assert TOX_INI.exists()


def test_tox_envlist_has_multiple_ansible_versions():
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    envlist = parser["tox"]["envlist"]
    # Format syntaxe tox range : ansible-2.{16,17,18}
    assert "ansible" in envlist, "envlist doit cibler ansible"
    assert "{" in envlist, "Doit utiliser la syntaxe range tox {16,17,18}"
    # Au moins une version récente d'ansible-core
    assert any(v in envlist for v in ["16", "17", "18"]), (
        f"envlist doit cibler 2.16/2.17/2.18, vu : {envlist}"
    )


def test_testenv_runs_molecule_test():
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    assert "testenv" in parser
    cmds = parser["testenv"].get("commands", "")
    assert "molecule test" in cmds


def test_at_least_3_envs_per_version():
    """Au moins 3 environnements [testenv:ansible-X] (multi-version)."""
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    ansible_envs = [s for s in parser.sections() if s.startswith("testenv:ansible-")]
    assert len(ansible_envs) >= 3, (
        f"Au moins 3 envs ansible-X attendus, vu : {ansible_envs}"
    )


def test_each_env_pins_ansible_core():
    """Chaque [testenv:ansible-X] pin une version d'ansible-core."""
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    for s in parser.sections():
        if s.startswith("testenv:ansible-"):
            deps = parser[s].get("deps", "")
            assert "ansible-core" in deps, f"{s} doit pinner ansible-core"


def test_lint_env_present():
    """Un env [testenv:lint] séparé pour fail-fast."""
    parser = configparser.ConfigParser()
    parser.read(TOX_INI)
    assert "testenv:lint" in parser
