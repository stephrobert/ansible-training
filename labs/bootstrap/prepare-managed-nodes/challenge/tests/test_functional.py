"""
Tests testinfra qui valident l'état post-run du lab 000-prepare-managed-nodes.

Ces tests se connectent aux 3 managed nodes (web1, web2, db1) via Ansible
en utilisant l'inventaire racine du lab. Ils vérifient que le playbook a
bien convergé.

Lancement depuis la racine du lab :
    pytest -v labs/bootstrap/prepare-managed-nodes/challenge/tests/

testinfra ouvre une connexion par hôte et reproduit `assert host.package(...)`
sans dépendre d'un wrapper SSH manuel — il s'appuie sur Ansible.
"""

import re

import pytest

from conftest import lab_host, assert_idempotent


# Hôtes managés (correspondent au groupe `rhce_lab` de l'inventaire)
MANAGED_NODES = ["web1.lab", "web2.lab", "db1.lab"]

# Tous les nœuds du lab : les 3 managed nodes + le control node. Ce sont les
# quatre noms que chaque managed node doit savoir résoudre.
LAB_NODES = ["control-node.lab"] + MANAGED_NODES


def _adresse_reelle(node):
    """Adresse IPv4 que le nœud porte VRAIMENT, demandée au nœud lui-même.

    Aucune IP n'est écrite dans ce fichier. Terraform les attribue, et la table
    figée qui trônait ici (10.10.20.10/.21/.22/.31) ne désignait aucune machine
    existante : le playbook du lab écrivait ces constantes dans /etc/hosts, le
    test cherchait les mêmes constantes, et l'ensemble était vert alors que les
    nœuds ne se résolvaient EN RIEN. Un test qui relit la valeur écrite par le
    code qu'il teste ne prouve rien : on interroge donc la machine.
    """
    sortie = lab_host(node).check_output("ip -4 -o addr show scope global")
    m = re.search(r"\binet (\d+\.\d+\.\d+\.\d+)/", sortie)
    assert m, f"Aucune IPv4 globale trouvée sur {node} : {sortie!r}"
    return m.group(1)


@pytest.fixture(scope="module")
def adresses_reelles():
    """Table {nom du nœud → son adresse réelle}, construite à l'exécution."""
    return {node: _adresse_reelle(node) for node in LAB_NODES}


@pytest.fixture(scope="module", params=MANAGED_NODES)
def host(request):
    """Connexion testinfra via SSH direct avec clé absolue (cf. conftest.py)."""
    return lab_host(request.param)


def test_chrony_installed_and_running(host):
    """chrony doit être installé et le service chronyd actif."""
    assert host.package("chrony").is_installed
    chronyd = host.service("chronyd")
    assert chronyd.is_enabled
    assert chronyd.is_running


def test_required_packages_installed(host):
    """Les paquets nécessaires à Ansible doivent être présents."""
    for pkg in ["python3-libselinux", "python3-firewall", "tar", "rsync"]:
        assert host.package(pkg).is_installed, f"{pkg} manquant"


def test_etc_hosts_contains_all_lab_nodes(host, adresses_reelles):
    """/etc/hosts doit mapper les 4 hôtes du lab sur leurs VRAIES adresses."""
    hosts_file = host.file("/etc/hosts")
    assert hosts_file.exists
    contenu = hosts_file.content_string
    for node, ip in adresses_reelles.items():
        court = node.split(".")[0]
        attendu = rf"^{re.escape(ip)}\s+.*\b{re.escape(court)}\b"
        assert re.search(attendu, contenu, re.M), (
            f"/etc/hosts de {host.backend.hostname} ne mappe pas {node} sur son "
            f"adresse réelle {ip}.\nContenu :\n{contenu}"
        )


def test_resolution_croisee_des_noeuds(host, adresses_reelles):
    """Chaque managed node RÉSOUT les autres nœuds sur leur adresse réelle.

    Le point 2 du scénario ne demande pas une ligne dans un fichier, il demande
    que la résolution FONCTIONNE. `getent hosts` interroge le résolveur du
    système : c'est le seul verdict qui compte, et il reste vrai si l'apprenant
    passe par autre chose que /etc/hosts.

    Le nœud lui-même est exclu : cloud-init pose `127.0.0.1 <nom>.lab.lab
    <nom>.lab` sur chaque machine, et cette ligne gagne pour son propre nom.
    C'est l'état livré par l'image, pas le travail de l'apprenant.
    """
    moi = host.backend.hostname
    for node, ip in adresses_reelles.items():
        if node == moi:
            continue
        resolu = host.run(f"getent hosts {node}")
        assert resolu.rc == 0, (
            f"{moi} ne résout pas du tout {node} : « getent hosts {node} » "
            f"sort en rc={resolu.rc}."
        )
        assert resolu.stdout.split()[0] == ip, (
            f"{moi} résout {node} sur {resolu.stdout.split()[0]}, alors que "
            f"{node} porte réellement {ip}. Une entrée /etc/hosts figée sur une "
            "adresse morte donne exactement ce résultat."
        )


def test_selinux_enforcing(host):
    """SELinux doit être en mode enforcing avec la policy targeted."""
    selinux = host.run("getenforce")
    assert selinux.stdout.strip() == "Enforcing", \
        f"SELinux n'est pas Enforcing : {selinux.stdout!r}"


def test_timezone_paris(host):
    """La timezone doit être Europe/Paris."""
    tz = host.run("timedatectl show --value -p Timezone")
    assert tz.stdout.strip() == "Europe/Paris"


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
