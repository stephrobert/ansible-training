"""
Configuration pytest globale pour le repo ansible-training.

Expose une fonction helper `lab_host(name)` qui construit une connexion
testinfra avec backend ssh:// et chemin de clé absolu — testinfra
ansible:// ne sait pas résoudre {{ playbook_dir }} et le DNS libvirt
n'est pas accessible depuis le control node, donc on bypass tout en
passant directement l'IP + la clé absolue.

Usage typique dans un test :

    from conftest import lab_host
    import pytest

    @pytest.fixture(scope="module")
    def host():
        return lab_host("db1.lab")
"""

import os
from pathlib import Path

import testinfra

REPO_ROOT = Path(__file__).parent.resolve()
SSH_KEY = REPO_ROOT / "ssh" / "id_ed25519"

# IP statiques (alignées sur les baux DHCP fixes du réseau libvirt lab-ansible).
LAB_HOSTS = {
    "control-node.lab": "10.10.20.10",
    "web1.lab": "10.10.20.21",
    "web2.lab": "10.10.20.22",
    "db1.lab": "10.10.20.31",
}

# Pour les sous-processus Ansible éventuels (ansible-playbook, ansible-inventory)
# lancés depuis pytest (rare, mais inoffensif).
os.environ.setdefault("ANSIBLE_PRIVATE_KEY_FILE", str(SSH_KEY))


def lab_host(name):
    """Retourne un host testinfra connecté en SSH direct avec la clé du lab.

    Args:
        name: hostname court ou FQDN (ex: "web1.lab", "db1.lab").

    Returns:
        testinfra Host prêt à l'usage (sudo activé via ansible NOPASSWD).
    """
    if name not in LAB_HOSTS:
        raise ValueError(
            f"Host inconnu : {name}. Hôtes disponibles : {list(LAB_HOSTS)}"
        )
    ip = LAB_HOSTS[name]
    extra = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    return testinfra.get_host(
        f"ssh://ansible@{ip}"
        f"?ssh_identity_file={SSH_KEY}"
        f"&ssh_extra_args={extra}"
        f"&sudo=true"
    )
