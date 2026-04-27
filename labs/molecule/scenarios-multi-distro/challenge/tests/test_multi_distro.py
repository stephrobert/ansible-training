"""Tests structure multi-distro."""

from pathlib import Path

import yaml

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"
ROLE_DIR = LAB_ROOT / "roles" / "webserver"


def test_vars_redhat_present():
    assert (ROLE_DIR / "vars/RedHat.yml").exists()


def test_vars_debian_present():
    assert (ROLE_DIR / "vars/Debian.yml").exists()


def test_tasks_uses_include_vars_dynamic():
    """tasks/main.yml charge dynamiquement vars/{{ ansible_os_family }}.yml."""
    content = (ROLE_DIR / "tasks/main.yml").read_text()
    assert "include_vars" in content
    assert "ansible_os_family" in content


def test_tasks_uses_package_module():
    """Module 'package' (agnostique) au lieu de dnf:/apt:."""
    content = (ROLE_DIR / "tasks/main.yml").read_text()
    assert "ansible.builtin.package:" in content
    assert "ansible.builtin.dnf:" not in content
    assert "ansible.builtin.apt:" not in content


def test_molecule_yml_has_at_least_3_platforms():
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    assert len(config["platforms"]) >= 3, "Doit tester sur au moins 3 distros"


def test_html_dir_diverges_between_distros():
    """RedHat et Debian ont des HTML dirs différents."""
    redhat = yaml.safe_load((ROLE_DIR / "vars/RedHat.yml").read_text())
    debian = yaml.safe_load((ROLE_DIR / "vars/Debian.yml").read_text())
    assert redhat["__webserver_html_dir"] != debian["__webserver_html_dir"]


def test_user_diverges_between_distros():
    """nginx user diffère : nginx (RHEL) vs www-data (Debian)."""
    redhat = yaml.safe_load((ROLE_DIR / "vars/RedHat.yml").read_text())
    debian = yaml.safe_load((ROLE_DIR / "vars/Debian.yml").read_text())
    assert redhat["__webserver_user"] == "nginx"
    assert debian["__webserver_user"] == "www-data"
