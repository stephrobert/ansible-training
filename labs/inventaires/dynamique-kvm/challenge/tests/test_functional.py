"""Tests pytest+testinfra pour le challenge inventaire dynamique KVM.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import subprocess

import pytest

from conftest import REPO_ROOT, assert_idempotent, lab_host, message

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
    assert f.exists, message(
        en=f"Marker missing on {name}: {marker}. The dynamic inventory did "
           f"not reach this VM, or the pattern excludes it.",
        fr=f"Marqueur manquant sur {name} : {marker}. L'inventaire dynamique "
           f"n'a pas atteint cette VM, ou le pattern l'exclut.",
    )
    assert f.mode == 0o644, message(
        en=f"The marker on {name} is {oct(f.mode)}, expected 0644.",
        fr=f"Le marqueur de {name} est en {oct(f.mode)}, attendu 0644.",
    )


def test_marker_content(vm):
    """Le contenu du marqueur prouve que l'inventaire dynamique a bien identifié la VM."""
    name, host = vm
    marker = f"/tmp/lab57-mark-{name}.txt"
    content = host.file(marker).content_string
    assert name in content, message(
        en=f"The marker does not carry {name}: the name must come from "
           f"inventory_hostname, which the libvirt plugin fills with the "
           f"domain's name.",
        fr=f"Le marqueur ne porte pas {name} : le nom doit venir "
           f"d'inventory_hostname, que le plugin libvirt remplit avec le nom "
           f"du domaine.",
    )
    assert "running" in content, message(
        en="The marker does not carry « running »: that state comes from the "
           "plugin, which is exactly what a static inventory could not know.",
        fr="Le marqueur ne porte pas « running » : cet état vient du plugin, "
           "et c'est précisément ce qu'un inventaire statique ne saurait pas.",
    )
    assert "inventaire dynamique libvirt OK" in content, message(
        en="The marker does not carry the expected sentence.",
        fr="Le marqueur ne porte pas la phrase attendue.",
    )


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
        check=False,
    )
    assert res.returncode == 0, message(
        en=f"`ansible {PATTERN} --list-hosts` failed:\n{res.stderr}",
        fr=f"`ansible {PATTERN} --list-hosts` a échoué :\n{res.stderr}",
    )
    resolved = {
        line.strip()
        for line in res.stdout.splitlines()
        if line.strip() and not line.strip().startswith("hosts (")
    }
    assert resolved == set(LAB_VMS), message(
        en=f"The {PATTERN} pattern resolves to {sorted(resolved)}, expected "
           f"{sorted(LAB_VMS)}.\nOne host too many means the lab writes on a "
           f"VM that is not its own; one host short means the lab_vms group "
           f"filter no longer matches the real libvirt domain names.",
        fr=f"Le pattern {PATTERN} résout {sorted(resolved)}, attendu "
           f"{sorted(LAB_VMS)}.\nUn hôte en trop, et le lab écrit sur une VM "
           f"qui n'est pas la sienne ; un hôte en moins, et le filtre du "
           f"groupe lab_vms ne correspond plus aux noms de domaines libvirt "
           f"réels.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
