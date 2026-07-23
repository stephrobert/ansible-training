"""Tests pytest+testinfra — lab navigator : ansible-navigator (EX294).

On prouve l'ÉTAT, pas la frappe :

- la PREUVE d'exploration existe sur db1.lab et cite le FQCN attendu (l'apprenant
  a bien lu la doc du module via `ansible-navigator doc`) ;
- le module découvert a réellement modifié le kernel de db1.lab (valeur live +
  fichier persistant) ;
- l'inventaire a été résolu par `ansible-navigator inventory` (la preuve contient
  l'hôte et le groupe déclarés) ;
- la solution est idempotente (critère RHCE).
"""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
DOC_PROOF = "/tmp/lab-navigator-doc.txt"
INV_PROOF = "/tmp/lab-navigator-inventory.txt"
SYSCTL_FILE = "/etc/sysctl.d/70-navigator-lab.conf"
EXPECTED_FQCN = "ansible.posix.sysctl"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_doc_proof_exists(host):
    f = host.file(DOC_PROOF)
    assert f.exists, (
        f"{DOC_PROOF} absent sur {TARGET_HOST} : la solution a-t-elle capturé la "
        "sortie de `ansible-navigator doc` et l'a-t-elle déposée ?"
    )


def test_doc_proof_mode_and_owner(host):
    f = host.file(DOC_PROOF)
    assert f.mode == 0o644, f"Mode attendu 0644, vu : {oct(f.mode)}"
    assert f.user == "root", f"Owner attendu root, vu : {f.user}"


def test_doc_proof_contains_expected_fqcn(host):
    """La preuve d'exploration doit citer le FQCN du module découvert.

    C'est ce qui distingue « j'ai lu la doc du module de la collection » d'un
    fichier vide : la sortie de `ansible-navigator doc ansible.posix.sysctl`
    contient l'en-tête `> MODULE ansible.posix.sysctl (...)`.
    """
    content = host.file(DOC_PROOF).content_string
    assert EXPECTED_FQCN in content, (
        f"{DOC_PROOF} ne cite pas {EXPECTED_FQCN} : la preuve doit être la sortie "
        f"de `ansible-navigator doc {EXPECTED_FQCN} --mode stdout`.\n"
        f"Contenu (200 c.) : {content[:200]}"
    )


def test_sysctl_value_applied_live(host):
    """Le module découvert a bien changé la valeur kernel LIVE de db1.lab."""
    value = host.sysctl("vm.swappiness")
    assert value == 42, (
        "vm.swappiness doit valoir 42 sur db1.lab (posé par le module découvert "
        f"ansible.posix.sysctl), vu : {value}"
    )


def test_sysctl_file_persistent(host):
    """La valeur doit être écrite dans un fichier /etc/sysctl.d/ (persistance)."""
    f = host.file(SYSCTL_FILE)
    assert f.exists, (
        f"{SYSCTL_FILE} absent : le module doit écrire le paramètre dans "
        "/etc/sysctl.d/ (sinon la valeur ne survit pas au reboot)."
    )
    content = f.content_string
    assert "vm.swappiness" in content and "42" in content, (
        f"{SYSCTL_FILE} doit contenir `vm.swappiness = 42`.\nContenu : {content!r}"
    )


def test_inventory_proof_resolves_host_and_group(host):
    """La preuve d'inventaire doit montrer que navigator a résolu notre inventaire.

    `ansible-navigator inventory --list` rend un JSON : il doit contenir l'hôte
    `db1.lab` ET le groupe `webservers` qu'on a déclaré. Un inventaire non parsé
    ne montrerait ni l'un ni l'autre.
    """
    f = host.file(INV_PROOF)
    assert f.exists, (
        f"{INV_PROOF} absent : la solution a-t-elle validé un inventaire avec "
        "`ansible-navigator inventory --list` et déposé sa sortie ?"
    )
    content = f.content_string
    assert "db1.lab" in content, (
        f"{INV_PROOF} ne mentionne pas db1.lab : l'inventaire validé doit le "
        f"contenir.\nContenu (200 c.) : {content[:200]}"
    )
    assert "webservers" in content, (
        f"{INV_PROOF} ne mentionne pas le groupe webservers : preuve que "
        "`ansible-navigator inventory` a bien parsé VOTRE inventaire structuré."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas idempotent,
    même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
