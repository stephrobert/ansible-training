"""Tests pytest+testinfra du challenge dependencies.

On ne lit pas meta/main.yml : on prouve sur db1.lab que les dépendances
ont tourné AVANT le rôle webserver (fichier d'ordre /tmp/deps-order.txt
alimenté par chaque rôle), avec les variables passées par la déclaration
(SELinux enforcing, port 443/tcp), et que le rôle parent a convergé.
Le module orchestre lui-même le run pour repartir d'une trace vierge.
"""

import os
import subprocess
from pathlib import Path

import pytest
import yaml

# REPO_ROOT vient de conftest : le compter en parents[] depuis ce fichier donnait
# labs/ (un cran trop bas), donc un cwd sans ansible.cfg (ni inventaire, ni clé).
from conftest import (
    REPO_ROOT,
    lab_host,
    lab_playbook,
    lab_solution_text,
    assert_idempotent,
)

# Ne JAMAIS poser LAB_NO_REPLAY ici : `os.environ[...]` au niveau module
# s'exécute à la COLLECTE, donc avant le premier test de la session, et pour
# TOUTE la session. Ce module désactivait ainsi le replay des solutions de
# `_apply_lab_state` pour tous les autres labs : chacun notait l'état laissé
# par son prédécesseur sur db1 (partagé) au lieu du sien. Résultat, la section
# passait lab par lab et échouait en bloc. Le replay du conftest est inoffensif
# ici : `_converge` repart de toute façon d'une trace vierge.

LAB_ROOT = Path(__file__).resolve().parents[2]
META_MAIN = LAB_ROOT / "roles/webserver/meta/main.yml"


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


@pytest.fixture(scope="module", autouse=True)
def _meta_dependencies():
    """Garantit que le meta/main.yml du rôle webserver déclare ses dépendances.

    Ce lab exige DEUX artefacts : le playbook (solution.yml) ET le meta/main.yml
    du rôle, qui porte tout le sens de l'exercice. Or le conftest racine
    n'arbitre que solution.yml : la référence du formateur
    (solution/roles/dependencies/meta-main.yml) n'était donc posée par personne.
    Le rôle gardait `dependencies: []`, les prérequis ne tournaient jamais et la
    trace d'ordre ne contenait que « webserver ».

    Si l'apprenant a complété le fichier, on n'y touche pas : c'est son travail
    qui est évalué, et un `dependencies:` faux doit continuer d'échouer. Sinon
    on installe la référence pour la durée du module, puis on restaure le
    dépôt à l'octet près (rien de la référence ne reste en clair dans labs/,
    où l'apprenant la lirait).
    """
    original = META_MAIN.read_text(encoding="utf-8")
    if (yaml.safe_load(original) or {}).get("dependencies"):
        yield  # travail de l'apprenant : on l'évalue tel quel
        return

    reference = yaml.safe_load(lab_solution_text(__file__, name="meta-main.yml"))
    patched = yaml.safe_load(original)
    # Seule la clé dependencies change : galaxy_info reste celui du lab.
    patched["dependencies"] = reference["dependencies"]
    META_MAIN.write_text(
        yaml.safe_dump(patched, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    try:
        yield
    finally:
        META_MAIN.write_text(original, encoding="utf-8")


@pytest.fixture(scope="module", autouse=True)
def _converge(_meta_dependencies):
    """Efface la trace d'ordre puis joue la solution (apprenant, sinon référence).

    Sans ce reset, une trace laissée par un run précédent (avec un
    meta/main.yml encore faux) fausserait la preuve d'ordre.
    """
    subprocess.run(
        [
            "ansible", "db1.lab", "-b",
            "-m", "ansible.builtin.shell",
            "-a", "rm -f /tmp/deps-order.txt",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    # La référence du formateur est chiffrée : sans vault_args, ansible-playbook
    # ne lit que du $ANSIBLE_VAULT.
    playbook, vault_args = lab_playbook(__file__)
    env = os.environ.copy()
    env["ANSIBLE_ROLES_PATH"] = "labs/roles/dependencies/roles"
    result = subprocess.run(
        ["ansible-playbook", *vault_args, str(playbook)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"solution.yml a échoué (exit {result.returncode})\n"
            f"--- stdout ---\n{result.stdout[-2000:]}\n"
            f"--- stderr ---\n{result.stderr[-1000:]}"
        )


def test_ordre_dependances_puis_role(db1):
    """LA preuve du lab : les dépendances ont tourné avant, dans l'ordre.

    Chaque rôle appose sa ligne dans /tmp/deps-order.txt au moment où il
    s'exécute. Si le fichier ne contient que 'webserver', les dependencies:
    ne sont pas déclarées. Si l'ordre diffère, la déclaration est inversée.
    """
    trace = db1.file("/tmp/deps-order.txt")
    assert trace.exists, (
        "/tmp/deps-order.txt absent : aucun rôle n'a tourné sur db1."
    )
    lines = trace.content_string.split()
    assert lines == ["selinux_setup", "firewall_setup", "webserver"], (
        f"Ordre d'exécution constaté : {lines}. Attendu : selinux_setup, "
        "firewall_setup, webserver. Les dépendances déclarées dans "
        "meta/main.yml s'exécutent AVANT le rôle, dans l'ordre de déclaration."
    )


def test_selinux_enforcing(db1):
    """La dépendance selinux_setup a reçu et appliqué selinux_state."""
    assert db1.run("getenforce").stdout.strip() == "Enforcing", (
        "SELinux n'est pas en Enforcing : la dépendance selinux_setup n'a "
        "pas tourné ou n'a pas reçu selinux_setup_state=enforcing."
    )


def test_firewalld_demarre_et_active(db1):
    svc = db1.service("firewalld")
    assert svc.is_running, (
        "firewalld doit être démarré : c'est le travail de firewall_setup, "
        "déclenché par la dépendance."
    )
    assert svc.is_enabled


def test_port_443_ouvert_par_la_dependance(db1):
    """Seule la dépendance ouvre 443/tcp : le rôle webserver ne le fait pas.

    C'est la preuve du passage de variables aux dépendances
    (firewall_open_ports dans la déclaration).
    """
    ports = db1.run("firewall-cmd --list-ports").stdout
    assert "443/tcp" in ports, (
        f"Ports ouverts : {ports.strip() or '(aucun)'}. 443/tcp manque : la "
        "dépendance firewall_setup n'a pas reçu "
        "firewall_setup_open_ports=['443/tcp']."
    )


def test_nginx_deploye_par_le_role_parent(db1):
    assert db1.package("nginx").is_installed
    svc = db1.service("nginx")
    assert svc.is_running, "nginx doit être démarré par le rôle webserver."
    assert svc.is_enabled
    assert db1.socket("tcp://0.0.0.0:8081").is_listening, (
        "nginx n'écoute pas sur 8081 : webserver_listen_port n'a pas été "
        "passé au rôle dans solution.yml."
    )


def test_port_8081_ouvert_par_le_role(db1):
    ports = db1.run("firewall-cmd --list-ports").stdout
    assert "8081/tcp" in ports, (
        "8081/tcp fermé : le rôle webserver ouvre lui-même son port "
        "d'écoute, mais il lui faut firewalld déjà démarré, ce que garantit "
        "la dépendance firewall_setup."
    )


def test_page_accueil(db1):
    index = db1.file("/usr/share/nginx/html/index.html")
    assert index.exists
    assert "Hello from db1.lab" in index.content_string


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
