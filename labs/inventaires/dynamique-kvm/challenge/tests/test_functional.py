"""Tests pytest+testinfra pour le challenge inventaire dynamique KVM."""

import subprocess

import pytest

from conftest import REPO_ROOT, lab_host, assert_idempotent

# Les 4 VMs du lab, nommées comme le domaine libvirt (`virsh list --all`).
# C'est aussi le nom que remonte `inventory_hostname: name`, et celui du bloc
# `Host` du ssh_config généré par dsoxlab : un seul nom, aucune traduction.
LAB_VMS = ["control-node.lab", "web1.lab", "web2.lab", "db1.lab"]

INVENTORY = "labs/inventaires/dynamique-kvm/inventory/"

# Le pattern que doit cibler la solution : intersection de la liste blanche
# statique et de l'état réel remonté par le plugin.
PATTERN = "lab_vms:&state_running"


@pytest.fixture(scope="module", params=LAB_VMS)
def vm(request):
    """Fixture paramétrique : retourne (nom_libvirt, host_testinfra)."""
    return request.param, lab_host(request.param)


def test_marker_exists(vm):
    """Le marqueur existe sur chaque VM running du lab."""
    name, host = vm
    marker = f"/tmp/lab57-mark-{name}.txt"
    f = host.file(marker)
    assert f.exists, f"Marqueur manquant sur {name}: {marker}"
    assert f.mode == 0o644


def test_marker_content(vm):
    """Le contenu du marqueur prouve que l'inventaire dynamique a bien identifié la VM."""
    name, host = vm
    marker = f"/tmp/lab57-mark-{name}.txt"
    content = host.file(marker).content_string
    assert name in content
    assert "running" in content
    assert "inventaire dynamique libvirt OK" in content


def test_pattern_ne_cible_que_les_vms_du_lab():
    """Le pattern de la solution ne doit JAMAIS toucher une VM hors formation.

    Le plugin libvirt remonte tous les domaines de la machine, y compris ceux
    qui n'ont rien à voir avec le lab (GitLab perso, nœuds Chef…). Un filtre
    relâché ferait écrire le playbook sur les machines personnelles de
    l'apprenant. On vérifie mécaniquement que le pattern résout exactement les
    4 VMs du lab, ni plus, ni moins.
    """
    res = subprocess.run(
        ["ansible", "-i", INVENTORY, PATTERN, "--list-hosts"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"`ansible {PATTERN} --list-hosts` a échoué :\n{res.stderr}"
    )
    resolved = {
        line.strip()
        for line in res.stdout.splitlines()
        if line.strip() and not line.strip().startswith("hosts (")
    }
    assert resolved == set(LAB_VMS), (
        f"Le pattern {PATTERN} résout {sorted(resolved)}, "
        f"attendu {sorted(LAB_VMS)}.\n"
        "Un hôte en trop = le lab écrit sur une VM qui n'est pas la sienne ; "
        "un hôte en moins = le filtre du groupe lab_vms ne matche plus les "
        "noms de domaines libvirt réels."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
