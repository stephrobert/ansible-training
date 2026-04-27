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

Fournit aussi une fixture `_apply_lab_state` (autouse, scope=module) qui
joue le `solution.yml` du challenge (ou le `playbook.yml` racine pour les
labs démo) avant les tests, pour que les labs passent indépendamment de
l'ordre. Cf. RECOMMANDATIONS — option (2).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import testinfra

REPO_ROOT = Path(__file__).parent.resolve()
SSH_KEY = REPO_ROOT / "ssh" / "id_ed25519"

# Rendre le package `progress` importable depuis n'importe quel CWD.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Plugin pytest qui inscrit chaque run dans la SQLite locale
# (~/.local/share/dsoxlab/progress.db). Désactivable via env DSOXLAB_DISABLED=1.
pytest_plugins = ["dsoxlab.pytest_plugin"]

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


# ----------------------------------------------------------------------
# Fixture auto : applique l'état du lab avant ses tests.
# ----------------------------------------------------------------------

# Pré-cleanups par lab (commande Ansible ad-hoc lancée AVANT solution.yml).
# Indispensable quand l'idempotence de solution.yml ne couvre pas un
# fichier annexe (ex : tag-reset.txt qu'un run --tags reset aurait créé).
# Les clés sont au format "<section>/<lab>" (chemin relatif depuis labs/).
_PRE_CLEANUPS = {
    "ecrire-code/tags": [
        "ansible", "db1.lab", "-b",
        "-m", "ansible.builtin.shell",
        "-a", "rm -f /tmp/challenge-tag-reset.txt",
    ],
    # Prépare /dev/loop10 vierge (200 MiB) avant le challenge parted.
    # On utilise loop10 (loin des loop bas occupés par le système) pour
    # éviter les conflits avec les snap/squashfs root.
    "modules-rhel/parted": [
        "ansible", "db1.lab", "-b",
        "-m", "ansible.builtin.shell",
        "-a",
        "umount /dev/loop10p* 2>/dev/null; "
        "losetup -d /dev/loop10 2>/dev/null; "
        "rm -f /var/tmp/lab-disk.img && "
        "dd if=/dev/zero of=/var/tmp/lab-disk.img bs=1M count=200 status=none && "
        "mknod -m 660 /dev/loop10 b 7 10 2>/dev/null; chown root:disk /dev/loop10 2>/dev/null; "
        "losetup -P /dev/loop10 /var/tmp/lab-disk.img && "
        "parted -s /dev/loop10 mklabel gpt",
    ],
    # Prépare /dev/loop10 (900 MiB) déjà partitionné en 2 (≥400 MiB chacune
    # pour xfs) avant le challenge filesystem.
    "modules-rhel/filesystem": [
        "ansible", "db1.lab", "-b",
        "-m", "ansible.builtin.shell",
        "-a",
        "umount /dev/loop10p* 2>/dev/null; "
        "losetup -d /dev/loop10 2>/dev/null; "
        "rm -f /var/tmp/lab-fs.img && "
        "dd if=/dev/zero of=/var/tmp/lab-fs.img bs=1M count=900 status=none && "
        "mknod -m 660 /dev/loop10 b 7 10 2>/dev/null; chown root:disk /dev/loop10 2>/dev/null; "
        "losetup -P /dev/loop10 /var/tmp/lab-fs.img && "
        "parted -s /dev/loop10 mklabel gpt mkpart p1 1MiB 450MiB mkpart p2 450MiB 100% && "
        "partprobe /dev/loop10",
    ],
}

# Args additionnels à passer à ansible-playbook par lab.
# Les clés sont au format "<section>/<lab>".
_EXTRA_ARGS = {
    "premiers-pas/ansible-vault": [
        "--vault-password-file",
        "labs/premiers-pas/ansible-vault/challenge/.vault_password",
    ],
    "ecrire-code/tags": ["--tags", "configuration"],
    "ecrire-code/variables-base": [
        "--extra-vars", "service_name=production-api db_max_connections=500",
    ],
    "ecrire-code/precedence-variables": [
        "--extra-vars", "winner=extra_vars_wins",
    ],
    "ecrire-code/conditions-when": [
        "--extra-vars", "enable_feature=true",
    ],
    "inventaires/group-vars-host-vars": [
        "-i", "labs/inventaires/group-vars-host-vars/inventory/hosts.yml",
    ],
    "inventaires/dynamique-kvm": [
        "-i", "labs/inventaires/dynamique-kvm/inventory/",
    ],
    "vault/introduction": [
        "--vault-password-file", "labs/vault/introduction/.vault_password",
    ],
    "vault/chiffrer-fichier-variable": [
        "--vault-password-file", "labs/vault/chiffrer-fichier-variable/.vault_password",
        "-i", "labs/vault/chiffrer-fichier-variable/inventory/hosts.yml",
    ],
    "vault/id-multiples": [
        "--vault-id", "dev@labs/vault/id-multiples/.vault_password_dev",
        "--vault-id", "prod@labs/vault/id-multiples/.vault_password_prod",
        "-i", "labs/vault/id-multiples/inventory/hosts.yml",
    ],
    "vault/playbooks-mixtes": [
        "--vault-password-file", "labs/vault/playbooks-mixtes/.vault_password",
        "-i", "labs/vault/playbooks-mixtes/inventory/hosts.yml",
    ],
    "vault/dans-roles": [
        "--vault-password-file", "labs/vault/dans-roles/.vault_password",
    ],
    "rhce/mock-ex294": [
        "--vault-password-file", "labs/rhce/mock-ex294/.vault_password",
        "-i", "labs/rhce/mock-ex294/inventory/hosts.yml",
    ],
}

# Variables d'environnement additionnelles par lab (utiles pour
# ANSIBLE_ROLES_PATH / ANSIBLE_COLLECTIONS_PATH qui ne se configurent pas
# via `-e` Ansible). Les clés sont au format "<section>/<lab>".
_EXTRA_ENV = {
    "roles/creer-premier-role": {
        "ANSIBLE_ROLES_PATH": "labs/roles/creer-premier-role/challenge/roles",
    },
    "vault/dans-roles": {
        "ANSIBLE_ROLES_PATH": "labs/vault/dans-roles/roles",
    },
    "collections/migration-role": {
        "ANSIBLE_COLLECTIONS_PATH": "labs/collections/migration-role/challenge/ansible_collections",
    },
    "rhce/mock-ex294": {
        "ANSIBLE_ROLES_PATH": "labs/rhce/mock-ex294/roles",
    },
}


def _find_lab_root(test_path):
    """Remonte les parents pour trouver labs/<section>/<lab>/.
    Retourne None si le test n'est pas dans un lab.

    Hiérarchie : <test_path> → tests → challenge → <lab> → <section> → labs → REPO_ROOT.
    Le "lab root" est le dossier <lab>, donc parent.parent.parent = REPO_ROOT/labs/<section>.
    """
    labs_dir = REPO_ROOT / "labs"
    for parent in test_path.parents:
        # Le lab root est le dossier dont le grand-parent est `labs/`.
        try:
            rel = parent.relative_to(labs_dir)
        except ValueError:
            continue
        # rel doit être de la forme <section>/<lab>, donc 2 composants.
        if len(rel.parts) == 2:
            return parent
    return None


def _lab_key(lab_root: Path) -> str:
    """Retourne la clé `<section>/<lab>` utilisée dans _EXTRA_ARGS / _EXTRA_ENV."""
    rel = lab_root.relative_to(REPO_ROOT / "labs")
    return rel.as_posix()


def _run(cmd, **kwargs):
    """Exécute une commande, lève en cas d'échec avec stdout/stderr lisibles."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(
            f"Commande échouée (exit {result.returncode}) : {' '.join(cmd)}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
    return result


@pytest.fixture(scope="module", autouse=True)
def _apply_lab_state(request):
    """Joue la solution du lab avant ses tests pour garantir l'isolation.

    - Lab démo (`Makefile` + `playbook.yml` racine, pas de challenge/solution.yml) :
      lance `make setup` puis `ansible-playbook playbook.yml`.
    - Lab pédagogique avec challenge Ansible (`challenge/solution.yml`) :
      lance `ansible-playbook challenge/solution.yml` (+ args si lab spécifique).
    - Lab pédagogique avec challenge Bash (`challenge/solution.sh`) ou
      sans solution Ansible : no-op (le test exécute lui-même le script).

    Si le `solution.yml`/`solution.sh` est absent, **skippe** le module avec
    un message explicite — l'apprenant doit l'écrire avant de lancer pytest.

    Activée par défaut sur tous les modules de test. Se désactive en
    posant la variable d'environnement `LAB_NO_REPLAY=1`.
    """
    if os.environ.get("LAB_NO_REPLAY") == "1":
        return

    test_path = Path(str(request.fspath)).resolve()
    lab_root = _find_lab_root(test_path)
    if lab_root is None:
        return  # test hors d'un lab

    lab_name = _lab_key(lab_root)  # ex : "vault/introduction"
    challenge_yml = lab_root / "challenge" / "solution.yml"
    challenge_sh = lab_root / "challenge" / "solution.sh"
    root_playbook = lab_root / "playbook.yml"
    makefile = lab_root / "Makefile"

    # Lab démo (Makefile + playbook.yml racine, pas de solution challenge)
    is_demo_lab = (
        makefile.exists()
        and root_playbook.exists()
        and not challenge_yml.exists()
        and not challenge_sh.exists()
    )

    if is_demo_lab:
        _run(["make", "setup"], cwd=lab_root)
        _run(
            ["ansible-playbook", str(root_playbook.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
        )
        return

    # Lab pédagogique : challenge/solution.yml requis (écrit par l'apprenant)
    if not challenge_yml.exists() and not challenge_sh.exists():
        pytest.skip(
            f"[{lab_name}] Aucun challenge/solution.yml ni solution.sh trouvé. "
            f"L'apprenant doit l'écrire en suivant challenge/README.md, puis "
            f"relancer pytest. (Désactive cette fixture avec LAB_NO_REPLAY=1)"
        )

    # Pré-cleanup spécifique au lab (avant tout play).
    pre = _PRE_CLEANUPS.get(lab_name)
    if pre:
        _run(pre, cwd=REPO_ROOT)

    if challenge_yml.exists():
        cmd = ["ansible-playbook", str(challenge_yml.relative_to(REPO_ROOT))]
        cmd += _EXTRA_ARGS.get(lab_name, [])
        env = os.environ.copy()
        env.update(_EXTRA_ENV.get(lab_name, {}))
        _run(cmd, cwd=REPO_ROOT, env=env)
    # Si seul solution.sh existe : le test l'exécute lui-même (no-op ici).
