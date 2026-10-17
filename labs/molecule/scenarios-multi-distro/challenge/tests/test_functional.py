"""Tests du lab 65 : portabilité multi-distro réalisée par l'apprenant.

Le rôle est livré mono-distro (dnf et chemins RHEL en dur) : ces tests ne
passent que lorsque l'apprenant l'a refactoré (include_vars dynamique,
module package, fichiers vars par famille) et a étendu la matrice
Molecule. `molecule syntax` est exécuté réellement en fin de parcours.
"""

import os
import shutil
import subprocess
from pathlib import Path

import yaml

from conftest import message

LAB_ROOT = Path(__file__).resolve().parents[2]
MOLECULE_DIR = LAB_ROOT / "molecule" / "default"
ROLE_DIR = LAB_ROOT / "roles" / "webserver"

VAR_KEYS = (
    "__webserver_package_name",
    "__webserver_service_name",
    "__webserver_html_dir",
    "__webserver_user",
)


def _vars(family):
    return yaml.safe_load((ROLE_DIR / "vars" / f"{family}.yml").read_text())


def test_vars_files_completed():
    for family in ("RedHat", "Debian"):
        data = _vars(family)
        for key in VAR_KEYS:
            value = data.get(key)
            assert value and value != "???", message(
                en=f"vars/{family}.yml: {key} is not filled in (seen {value!r})",
                fr=f"vars/{family}.yml : {key} n'est pas renseigné (vu {value!r})",
            )


def test_tasks_uses_include_vars_dynamic():
    content = (ROLE_DIR / "tasks/main.yml").read_text()
    assert "include_vars" in content and "ansible_os_family" in content, message(
        en="tasks/main.yml must load vars/{{ ansible_os_family }}.yml through "
        "include_vars: that is the mechanism that adapts the role to the family",
        fr="tasks/main.yml doit charger vars/{{ ansible_os_family }}.yml via "
        "include_vars : c'est le mécanisme qui adapte le rôle à la famille",
    )


def test_tasks_uses_package_module():
    content = (ROLE_DIR / "tasks/main.yml").read_text()
    assert "ansible.builtin.package:" in content, message(
        en="Use the agnostic ansible.builtin.package module for the install: "
        "one task for every family",
        fr="Utilisez le module agnostique ansible.builtin.package pour "
        "l'installation : une seule tâche pour toutes les familles",
    )
    assert "ansible.builtin.dnf:" not in content, message(
        en="No more dnf: in the role: it would break on Debian",
        fr="Plus de dnf: dans le rôle : il casserait sur Debian",
    )
    assert "ansible.builtin.apt:" not in content, message(
        en="No apt: either: the package module picks for itself",
        fr="Pas non plus de apt: : le module package choisit tout seul",
    )


def test_tasks_use_family_variables_not_hardcoded_paths():
    tasks = yaml.safe_load((ROLE_DIR / "tasks/main.yml").read_text())
    dumped = yaml.dump(tasks)
    assert "__webserver_html_dir" in dumped, message(
        en="The HTML directory must come from __webserver_html_dir (per-family "
        "vars), not from a hardcoded path",
        fr="Le répertoire HTML doit venir de __webserver_html_dir (vars par "
        "famille), pas d'un chemin en dur",
    )
    assert "__webserver_user" in dumped, message(
        en="The user must come from __webserver_user (nginx on RHEL, www-data "
        "on Debian)",
        fr="L'utilisateur doit venir de __webserver_user (nginx sur RHEL, "
        "www-data sur Debian)",
    )
    assert "/usr/share/nginx/html" not in dumped, message(
        en="A RHEL path is still hardcoded in tasks/main.yml: it must move to "
        "vars/RedHat.yml",
        fr="Chemin RHEL encore en dur dans tasks/main.yml : il doit migrer "
        "vers vars/RedHat.yml",
    )


def test_html_dir_diverges_between_distros():
    assert _vars("RedHat")["__webserver_html_dir"] != _vars("Debian")["__webserver_html_dir"], message(
        en="The RHEL and Debian HTML directories must differ: if your two vars "
        "files are identical, portability is not captured",
        fr="Les répertoires HTML RHEL et Debian doivent différer : si vos deux "
        "fichiers vars sont identiques, la portabilité n'est pas capturée",
    )


def test_user_diverges_between_distros():
    assert _vars("RedHat")["__webserver_user"] == "nginx", message(
        en="On the RedHat family, nginx runs as the nginx user",
        fr="Sur la famille RedHat, nginx tourne sous l'utilisateur nginx",
    )
    assert _vars("Debian")["__webserver_user"] == "www-data", message(
        en="On the Debian family, nginx runs as www-data",
        fr="Sur la famille Debian, nginx tourne sous www-data",
    )


def test_molecule_matrix_has_3_platforms_two_families():
    config = yaml.safe_load((MOLECULE_DIR / "molecule.yml").read_text())
    platforms = config.get("platforms") or []
    assert len(platforms) >= 3, message(
        en=f"At least 3 platforms expected in molecule.yml, seen: "
        f"{len(platforms)}. Portability is proven on a matrix",
        fr=f"Au moins 3 plateformes attendues dans molecule.yml, vu : "
        f"{len(platforms)}. La portabilité se prouve sur une matrice",
    )
    images = " ".join(str(p.get("image", "")) for p in platforms)
    assert any(s in images for s in ("debian", "ubuntu")), message(
        en="The matrix must include the Debian family (a debian or ubuntu "
        "image): testing 3 RHELs proves no portability at all",
        fr="La matrice doit inclure la famille Debian (image debian ou ubuntu) : "
        "tester 3 RHEL ne prouve aucune portabilité",
    )


def test_molecule_syntax_passes():
    """Exécute réellement `molecule syntax` sur le scénario refactoré."""
    assert shutil.which("molecule"), message(
        en="molecule is not on this machine: install it (pipx install molecule), "
        "it is the tool this section teaches",
        fr="molecule est introuvable sur le poste : installez-le "
        "(pipx install molecule), c'est l'outil enseigné par cette section",
    )
    env = dict(os.environ, ANSIBLE_ROLES_PATH=str(LAB_ROOT / "roles"))
    result = subprocess.run(
        ["molecule", "syntax"],
        cwd=LAB_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, message(
        en=f"`molecule syntax` fails:\n{result.stdout}{result.stderr}",
        fr=f"`molecule syntax` échoue :\n{result.stdout}{result.stderr}",
    )
