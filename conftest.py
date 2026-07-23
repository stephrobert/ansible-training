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
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
# testinfra n'est importé que dans lab_host(), à l'usage. Il ne sert qu'aux
# labs vm, alors qu'un import en tête de fichier casse le chargement de ce
# conftest pour TOUS les tests du dépôt, y compris les vérificateurs de
# catalogue de tests/ qui ne touchent jamais une machine. C'est ce qui faisait
# échouer le job « Pre-commit parity » : l'environnement isolé des hooks n'a
# pas testinfra.

REPO_ROOT = Path(__file__).parent.resolve()
SSH_KEY = REPO_ROOT / "ssh" / "id_ed25519"

# Ne collecter QUE les tests des challenges. Le contrat dsoxlab impose leur
# emplacement (challenge/tests/test_functional.py) : tout `test_*.py` ailleurs
# sous labs/ est un ARTEFACT du lab, pas un test du catalogue.
#
# `collect_ignore_glob` doit vivre ICI : ce n'est pas une option ini. Déclarée
# dans pyproject.toml, elle était rejetée en silence (« PytestConfigWarning:
# Unknown config option »), donc ces exclusions ne protégeaient de rien.
#
# Trois dégâts réels, mesurés, qu'elles évitent :
#
# 1. `labs/tests/testinfra/molecule/default/tests/test_webserver.py` était
#    collecté par le run global et exécuté en backend « local », c'est-à-dire
#    CONTRE LE POSTE du formateur : 3 tests sur 6 y passaient au vert (quelque
#    chose écoute sur 8080, un /etc/nginx/nginx.conf traîne). Des tests verts
#    qui n'ont jamais approché une VM du lab.
# 2. `galaxy/installer-roles` installe pour de vrai dans challenge/deps/ (son
#    test l'exige). Au run SUIVANT, pytest collectait les tests unitaires
#    embarqués dans les collections téléchargées et sortait en « Interrupted:
#    2 errors during collection » : zéro test exécuté sur TOUT le dépôt. Le
#    premier run passait, le second cassait tout.
# 3. `challenge/work/` reçoit le travail de l'apprenant sur les labs shell.
collect_ignore_glob = [
    "labs/*/*/molecule/*",
    "labs/*/*/**/ansible_collections/*",
    "labs/*/*/challenge/deps/*",
    "labs/*/*/challenge/work/*",
]

# Rendre le package `progress` importable depuis n'importe quel CWD.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Le suivi d'avancement est assuré par la CLI dsoxlab externe
# (`uv tool install dsoxlab`), qui enregistre les résultats de `dsoxlab check`
# dans sa propre base. Le plugin pytest embarqué qui tenait ce rôle a été retiré
# avec le package `dsoxlab/` vendored.

def _dsoxlab_ssh_config() -> Path | None:
    """Chemin du ssh_config généré par dsoxlab, ou None s'il n'existe pas.

    dsoxlab écrit un ssh_config OpenSSH depuis l'inventaire dynamique (outputs
    Terraform + meta.yml) : il porte les IP réelles, l'utilisateur, la clé. On
    le consomme au lieu de redéclarer tout ça, comme le fait le conftest de
    linux-dsoxlab-training.

    Les IP étaient codées en dur ici, héritées des baux statiques de l'ancien
    provision.sh. Terraform les attribue désormais dynamiquement : la table
    figée pointait quatre adresses mortes et AUCUN test ne joignait plus de VM.
    """
    for env in ("XDG_CACHE_HOME",):
        base = os.environ.get(env)
        if base:
            p = Path(base) / "dsoxlab" / "ansible-training" / "ssh_config"
            if p.is_file():
                return p
    p = Path.home() / ".cache" / "dsoxlab" / "ansible-training" / "ssh_config"
    return p if p.is_file() else None


# Pour les sous-processus Ansible éventuels (ansible-playbook, ansible-inventory)
# lancés depuis pytest (rare, mais inoffensif).
os.environ.setdefault("ANSIBLE_PRIVATE_KEY_FILE", str(SSH_KEY))


def lab_host(name):
    """Retourne un host testinfra connecté à une VM du lab.

    La connexion (IP, utilisateur, clé) vient du ssh_config généré par dsoxlab :
    aucune adresse n'est codée ici. On passe le nom d'hôte à testinfra via
    `?ssh_config=`, et OpenSSH résout le reste — plus fiable que de bourrer des
    options dans une URL, dont les espaces et quotes cassent le parser.

    Args:
        name: FQDN du lab (ex : "web1.lab", "db1.lab").

    Returns:
        testinfra Host prêt à l'usage (sudo activé).
    """

    try:
        import testinfra
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "testinfra est absent : les labs vm ont besoin de "
            "pytest-testinfra. Installe-le, ou lance les labs via "
            "'dsoxlab check', qui l'embarque."
        ) from exc
    cfg = _dsoxlab_ssh_config()
    if cfg is None:
        pytest.skip(
            "ssh_config dsoxlab introuvable : l'infrastructure n'est pas "
            "provisionnée. Lance `dsoxlab provision` puis réessaie."
        )
    known = [
        line.split()[1]
        for line in cfg.read_text(encoding="utf-8").splitlines()
        if line.startswith("Host ")
    ]
    if name not in known:
        raise ValueError(f"Host inconnu : {name}. Hôtes disponibles : {known}")
    return testinfra.get_host(f"ssh://{name}?ssh_config={cfg}&sudo=true")


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
    # Les labs de stockage (modules-rhel/parted, filesystem) travaillent sur
    # le disque secondaire réel /dev/vdb de db1.lab (meta.yml: extra_disk_gb).
    # La remise à zéro du disque vit dans le setup.yaml/cleanup.yaml de chaque
    # lab : plus de loop device fabriqué ici.
    #
    # mock-ex294-2 tâche 19 pose vm.swappiness=25 dans /etc/sysctl.d/99-lab200-*.
    # D'autres labs laissent leurs propres fichiers sur db1 (modules-rhel/sysctl
    # -> 99-rhce-lab.conf=10 ; collections/navigator -> 70-navigator-lab.conf=42).
    # Selon l'ordre lexicographique de lecture de systemd-sysctl, l'un d'eux peut
    # supplanter la valeur 25 au reboot et faire échouer test_99 (persistance).
    # On purge ces fichiers de labs AVANT de rejouer la solution ; le setup.yaml
    # du lab fait de même pour l'apprenant lancé via dsoxlab run.
    "rhce/mock-ex294-2": [
        "ansible", "db1.lab", "-b",
        "-m", "ansible.builtin.shell",
        "-a", "rm -f /etc/sysctl.d/*lab*.conf",
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
        # Pas de `-i` ici : il dépend du mode. Cf. _inventory_args.
    ],
    "rhce/mock-ex294-2": [
        "--vault-password-file", "labs/rhce/mock-ex294-2/.vault_password",
        # Pas de `-i` ici : il dépend du mode. Cf. _inventory_args.
    ],
}


_INVENTORY_LABS: dict = {}


def _inventory_args(lab_name: str, lab_root: Path) -> list[str]:
    """`-i` du lab, résolu selon le mode : travail de l'apprenant, sinon référence.

    Ne concerne que les labs dont l'INVENTAIRE est justement ce qu'il faut
    produire. Le capstone RHCE en est un : ses tâches 1 et 2 demandent d'écrire
    `inventory/hosts.yml` et ses group_vars/host_vars.

    Le conftest imposait le même `-i labs/rhce/mock-ex294/inventory/` aux deux
    modes. Il fallait donc committer cet inventaire pour que le mode formateur
    fonctionne, ce qui revenait à livrer au candidat la réponse aux deux
    premières tâches de son examen. La référence vit désormais sous solution/,
    chiffrée (ansible lit un inventaire vaulté, vérifié), et le dossier de
    l'apprenant est gitignoré comme sa solution.yml.
    """
    resolved = _resolve_inventory(lab_name, lab_root)
    if resolved is None:
        return []
    args = ["-i", str(resolved.relative_to(REPO_ROOT))]
    if resolved.is_relative_to(REPO_ROOT / "solution"):
        args += ["--vault-password-file", ".vault-pass"]
    return args


def _resolve_inventory(lab_name: str, lab_root: Path) -> Path | None:
    """Dossier d'inventaire en jeu : celui de l'apprenant, sinon la référence."""
    learner = lab_root / "inventory"
    if learner.is_dir() and any(learner.iterdir()):
        return learner
    reference = REPO_ROOT / "solution" / lab_name / "inventory"
    return reference if reference.is_dir() else None


def reboot_and_wait(name, timeout=300):
    """Redémarre une VM du lab et attend son retour. Rend un host testinfra frais.

    C'est le SEUL moyen de prouver la persistance. Les tests s'en remettent
    d'ordinaire à des indices : la colonne « persistant » de `semanage boolean
    -l`, `firewall-cmd --permanent`, une entrée dans /etc/fstab. Ce sont de bons
    indices, et ils valent mieux que rien, mais aucun ne prouve que la machine
    revient correcte : un fstab syntaxiquement valide peut faire échouer le
    boot, une règle permanente peut être masquée par une zone active
    différente. La persistance est justement le piège qui fait échouer les
    candidats RHCE, et un capstone qui la certifie sans jamais redémarrer
    certifie une hypothèse.

    Le module `reboot` d'Ansible attend lui-même le retour de la machine, y
    compris le retour de la connexion SSH : inutile de refaire cette boucle.

    Args:
        name: FQDN de la VM (ex : "db1.lab").
        timeout: secondes accordées au retour de la machine.

    Returns:
        Un host testinfra reconnecté.
    """
    _run(
        ["ansible", name, "-i", "inventory/hosts.yml", "-b",
         "-m", "ansible.builtin.reboot",
         "-a", f"reboot_timeout={timeout}"],
        cwd=REPO_ROOT,
    )
    return lab_host(name)


def lab_inventory_args(test_file):
    """Arguments `-i` (+ vault) de l'inventaire en jeu, pour un lab où il est le livrable.

    Même arbitrage que la fixture de replay : le travail de l'apprenant s'il
    existe, la référence chiffrée sinon. Pour les tests qui INSPECTENT
    l'inventaire (`ansible-inventory --graph`) : coder en dur le chemin de
    l'apprenant les rend infaisables en mode formateur, où il n'existe pas.

    Rend la liste complète d'arguments, et pas seulement le chemin : la
    référence est chiffrée, et un appelant qui oublierait le mot de passe
    obtiendrait « Attempting to decrypt but no vault secrets found », un échec
    sans rapport avec ce que le test cherche à prouver.

    Usage : subprocess.run(["ansible-inventory", *lab_inventory_args(__file__), "--graph"])
    """
    lab_root = _find_lab_root(Path(test_file))
    if lab_root is None:
        raise RuntimeError(f"Test hors d'un lab : {test_file}")
    lab_name = _lab_key(lab_root)
    resolved = _resolve_inventory(lab_name, lab_root)
    if resolved is None:
        pytest.skip(
            f"[{lab_name}] ni inventory/ (votre travail) ni "
            f"solution/{lab_name}/inventory/ (référence)."
        )
    args = ["-i", str(resolved.relative_to(REPO_ROOT))]
    if resolved.is_relative_to(REPO_ROOT / "solution"):
        vault_pass = REPO_ROOT / ".vault-pass"
        if not vault_pass.is_file():
            pytest.skip(
                f"[{lab_name}] inventaire de référence chiffré mais .vault-pass "
                "absent : impossible de le lire."
            )
        args += ["--vault-password-file", str(vault_pass.relative_to(REPO_ROOT))]
    return args

# Variables d'environnement additionnelles par lab, pour ce qui ne se configure
# ni via `-e` ni par convention. Les clés sont au format "<section>/<lab>".
#
# ANSIBLE_ROLES_PATH n'est PAS ici : il se déduit de l'arborescence du lab
# (cf. _roles_path). Cette table le listait lab par lab, et 8 labs à rôles y
# manquaient : ils ne cassaient pas, ils étaient juste skippés, donc invisibles.
_EXTRA_ENV = {
    "collections/migration-role": {
        "ANSIBLE_COLLECTIONS_PATH": "labs/collections/migration-role/challenge/ansible_collections",
    },
}


def _protect_lab_tree(request, lab_root: Path) -> None:
    """Restaure, après le module, les fichiers du lab que la référence a écrasés.

    Plusieurs labs d'outillage (ci, ee, galaxy, collections) ont pour livrable un
    SQUELETTE VERSIONNÉ que l'apprenant édite en place : un `.gitlab-ci.yml`
    truffé de `???`, un `requirements.yml` avec `roles: []`… Quand la référence
    tourne, elle écrit la correction PAR-DESSUS ces fichiers suivis. Sans
    restauration, un run laisse les réponses en clair dans l'arbre, et le
    prochain `git add` les commite. La branche solution.sh a son finalizer ;
    celle-ci n'avait rien.

    On ne restaure QUE les fichiers qui étaient propres avant notre passage :
    si l'apprenant a déjà modifié son squelette, c'est son travail, on n'y
    touche pas.
    """
    res = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no", "--", str(lab_root)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if res.returncode != 0:
        return  # hors dépôt git : rien à protéger
    deja_sales = {line[3:].strip() for line in res.stdout.splitlines()}

    def _restaurer() -> None:
        apres = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "--", str(lab_root)],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if apres.returncode != 0:
            return
        salis = {line[3:].strip() for line in apres.stdout.splitlines()} - deja_sales
        if salis:
            subprocess.run(
                ["git", "checkout", "--", *sorted(salis)],
                cwd=REPO_ROOT, capture_output=True, text=True,
            )

    request.addfinalizer(_restaurer)


def _decrypt(path: Path) -> str:
    """Contenu d'un fichier de référence, déchiffré si ansible-vault l'a chiffré.

    Les solutions de référence sont chiffrées : les lire telles quelles rend
    « $ANSIBLE_VAULT;1.1;AES256 », ce qui ne ressemble à rien de ce qu'un test
    cherche. Le déchiffrement se fait en mémoire, jamais sur le disque.
    """
    if not path.read_text(encoding="utf-8").startswith("$ANSIBLE_VAULT"):
        return path.read_text(encoding="utf-8")
    vault_pass = REPO_ROOT / ".vault-pass"
    if not vault_pass.is_file():
        pytest.skip(
            f"{path.relative_to(REPO_ROOT)} est chiffré mais .vault-pass est "
            "absent : impossible de le lire."
        )
    return _run(
        ["ansible-vault", "view",
         "--vault-password-file", str(vault_pass.relative_to(REPO_ROOT)),
         str(path.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
    ).stdout


def _roles_path(lab_root: Path) -> dict[str, str]:
    """ANSIBLE_ROLES_PATH déduit de l'arborescence du lab.

    Ansible résout les rôles relativement au dossier du PLAYBOOK. Une solution
    de référence vit dans solution/<lab>/, jamais dans labs/<lab>/ : sans cette
    variable, elle ne voit aucun des rôles du lab et sort sur « the role
    'webserver' was not found ».

    Ordre : le rôle écrit par l'apprenant (challenge/roles) prime sur celui
    livré avec le lab (roles/), ce qui est le sens de l'exercice quand les deux
    existent.
    """
    candidates = [lab_root / "challenge" / "roles", lab_root / "roles"]
    found = [str(p.relative_to(REPO_ROOT)) for p in candidates if p.is_dir()]
    return {"ANSIBLE_ROLES_PATH": ":".join(found)} if found else {}


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


# ── Isolation par overlay qcow2 (snapshot maison, compatible UEFI) ────────────
# Les VM du lab tournent en UEFI (pflash) : dsoxlab force `firmware = "efi"`
# dans son Terraform KVM, quelle que soit la distro. `virsh snapshot-revert` est
# refusé (snapshots internes interdits sur pflash, revert d'un snapshot externe
# rejeté). On obtient le même effet avec un overlay qcow2 jetable : le disque
# frais post-provision devient une base IMMUABLE (`<vol>.base.qcow2`) et la VM
# tourne sur un overlay (`<vol>.qcow2`, le nom déjà référencé par le domaine,
# donc aucune reconfiguration libvirt). Réinitialiser = recréer l'overlay vide
# sur la base : tout ce que le lab a écrit (fstab, sysctl.d, paquets, reboot)
# est jeté, la VM repart identique. Increvable : plus de cascade inter-labs.
#
# OPT-IN et sans effet tant qu'aucune base n'existe : un dépôt non basé se
# comporte exactement comme avant (setup.yaml + solution.yml). On crée les bases
# avec `snapshot_base()` sur des VM fraîches ; le reset par lab est automatique.

_LIBVIRT_POOL_DIR = Path("/var/lib/libvirt/images")


def _meta_vm_fqdns() -> list[str]:
    """FQDN de toutes les VM déclarées dans meta.yml (infra.hosts)."""
    import yaml as _yaml

    meta = _yaml.safe_load((REPO_ROOT / "meta.yml").read_text(encoding="utf-8")) or {}
    hosts = (meta.get("infra") or {}).get("hosts") or []
    return [h["name"] for h in hosts if isinstance(h, dict) and h.get("name")]


def _lab_vm_fqdns(lab_root: Path) -> list[str]:
    """FQDN des VM qu'un lab utilise : host du target résolu + ses roles.

    Ne reset que ces hôtes-là (pas les 4 VM) : chaque lab nettoie ce qu'il
    touche avant de le toucher, ce qui suffit à l'isolation et divise le temps
    du run global. Retourne [] pour un lab shell (pas de runtime vm).
    """
    import yaml as _yaml

    lab_yaml = lab_root / "lab.yaml"
    if not lab_yaml.exists():
        return []
    spec = _yaml.safe_load(lab_yaml.read_text(encoding="utf-8")) or {}
    runtime = spec.get("runtime") or {}
    targets = runtime.get("targets") or []
    if not targets:
        return []
    default = runtime.get("default")
    target = next((t for t in targets if t.get("name") == default), targets[0])
    fqdns: list[str] = []
    if target.get("host"):
        fqdns.append(target["host"])
    for role_host in (target.get("roles") or {}).values():
        if role_host:
            fqdns.append(role_host)
    return list(dict.fromkeys(fqdns))


def _domain_disks(domain: str) -> list[str]:
    """Chemins absolus des disques INSCRIPTIBLES (hors cdrom) d'un domaine."""
    res = subprocess.run(
        ["sudo", "virsh", "domblklist", domain, "--details"],
        capture_output=True, text=True,
    )
    disks: list[str] = []
    for line in res.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "disk":
            src = parts[3]
            disks.append(src if src.startswith("/") else str(_LIBVIRT_POOL_DIR / src))
    return disks


def _base_path(disk: str) -> str:
    """`/…/db1.lab.qcow2` → `/…/db1.lab.base.qcow2`."""
    if disk.endswith(".qcow2"):
        return disk[: -len(".qcow2")] + ".base.qcow2"
    return disk + ".base"


def _mem_save_path(fqdn: str) -> str:
    """Copie « golden » de l'état mémoire figé, réutilisée à chaque reset."""
    return str(_LIBVIRT_POOL_DIR / f"{fqdn}.mem.save")


def _managed_save_path(fqdn: str) -> str:
    """Emplacement où libvirt attend le managedsave d'un domaine.

    `virsh restore` ne marche pas sur nos domaines PERSISTANTS (« domain already
    exists ») : on passe donc par `virsh managedsave` (état lié au domaine, repris
    par `virsh start`). Pour réutiliser l'état N fois, on garde une copie golden et
    on la recopie ici avant chaque `start`.
    """
    return f"/var/lib/libvirt/qemu/save/{fqdn}.save"


def _wait_ssh(fqdns: list[str], timeout: int = 240) -> None:
    """Attend que chaque VM ait FINI de démarrer après un reset/reboot.

    Attendre que SSH réponde ne suffit pas : sshd ouvre bien avant que les
    services managés (firewalld, chronyd…) soient prêts, et un setup.yaml joué
    trop tôt lève (« INVALID_ZONE: Zone block is not available » quand firewalld
    n'a pas fini de charger ses zones). On attend donc `systemctl
    is-system-running` = `running`/`degraded` (boot terminé), pas juste le port.
    """
    cfg = _dsoxlab_ssh_config()
    if cfg is None:
        time.sleep(25)
        return
    for fqdn in fqdns:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            probe = subprocess.run(
                ["ssh", "-F", str(cfg), "-o", "ConnectTimeout=6",
                 "-o", "BatchMode=yes", fqdn,
                 "systemctl is-system-running 2>/dev/null || true"],
                capture_output=True, text=True,
            )
            if probe.stdout.strip() in ("running", "degraded"):
                break
            time.sleep(5)


def snapshot_base(fqdns: list[str]) -> None:
    """Prépare chaque VM pour l'isolation RAPIDE (à lancer sur des VM fraîches).

    1. Base immuable (`<vol>.base.qcow2`) + overlay remis à neuf → état propre.
    2. Boot complet (services prêts), puis on FIGE l'état mémoire (`virsh save`)
       ET le disque post-boot (`<vol>.qcow2.postboot`) : le reset se fera par
       `virsh restore` (quelques secondes, sans reboot) au lieu d'un boot complet.
    Idempotent (la base n'est créée qu'une fois ; l'overlay est toujours remis à
    neuf pour que l'état figé parte propre).
    """
    for fqdn in fqdns:
        subprocess.run(["sudo", "virsh", "destroy", fqdn], capture_output=True)
        for disk in _domain_disks(fqdn):
            base = _base_path(disk)
            if not Path(base).exists():
                _run(["sudo", "mv", disk, base])
            tmp = disk + ".new"
            _run(["sudo", "qemu-img", "create", "-f", "qcow2", "-F", "qcow2",
                  "-b", base, tmp])
            _run(["sudo", "mv", tmp, disk])
        _run(["sudo", "virsh", "pool-refresh", "default"])
        _run(["sudo", "virsh", "start", fqdn])
    _wait_ssh(fqdns)
    # Fige mémoire + disque post-boot COHÉRENTS (tous les disques inscriptibles,
    # pas seulement vda : db1 a aussi vdb). Le .postboot est copié pendant que la
    # VM est « saved » (disque quiescent), donc cohérent avec le .mem.save.
    for fqdn in fqdns:
        golden = _mem_save_path(fqdn)
        _run(["sudo", "virsh", "managedsave", fqdn])
        _run(["sudo", "cp", _managed_save_path(fqdn), golden])
        for disk in _domain_disks(fqdn):
            _run(["sudo", "cp", disk, disk + ".postboot"])
        _run(["sudo", "virsh", "start", fqdn])


def snapshot_reset(fqdns: list[str]) -> bool:
    """Reset chaque VM à son état de base propre. Retourne True si au moins une
    VM a été reset. No-op sur les VM non basées.

    Deux modes :
    - RAPIDE (par défaut si `snapshot_base` a figé un état mémoire) : restaure le
      disque post-boot cohérent + `virsh restore` de la mémoire. La VM revient
      déjà bootée, services up, en quelques secondes, SANS reboot.
    - REPLI : recrée l'overlay vide sur la base + `virsh start` (reboot complet),
      si aucun état mémoire figé n'existe.
    """
    reset_any = False
    for fqdn in fqdns:
        disks = _domain_disks(fqdn)
        if not disks:
            continue
        mem = _mem_save_path(fqdn)
        postboots = [d + ".postboot" for d in disks]
        if Path(mem).exists() and all(Path(p).exists() for p in postboots):
            reset_any = True
            subprocess.run(["sudo", "virsh", "destroy", fqdn], capture_output=True)
            for disk in disks:
                tmp = disk + ".new"
                _run(["sudo", "cp", disk + ".postboot", tmp])
                _run(["sudo", "mv", tmp, disk])
            _run(["sudo", "virsh", "pool-refresh", "default"])
            _run(["sudo", "cp", mem, _managed_save_path(fqdn)])
            _run(["sudo", "virsh", "start", fqdn])
            continue
        pairs = [(d, _base_path(d)) for d in disks]
        if not all(Path(b).exists() for _, b in pairs):
            continue
        reset_any = True
        subprocess.run(["sudo", "virsh", "destroy", fqdn], capture_output=True)
        for disk, base in pairs:
            tmp = disk + ".new"
            _run(["sudo", "qemu-img", "create", "-f", "qcow2", "-F", "qcow2",
                  "-b", base, tmp])
            _run(["sudo", "mv", tmp, disk])
        _run(["sudo", "virsh", "pool-refresh", "default"])
        _run(["sudo", "virsh", "start", fqdn])
    if reset_any:
        _wait_ssh(fqdns)
        _resync_clocks(fqdns)
    return reset_any


def _resync_clocks(fqdns: list[str]) -> None:
    """Force chaque VM restaurée à recaler son horloge sur NTP.

    `virsh managedsave` fige la MÉMOIRE : au restore, la VM reprend avec l'heure
    qu'il était au moment du snapshot. Deux VM restaurées à des instants
    différents divergent donc d'autant, et rien ne les rattrape : chrony est
    configuré en `makestep 1.0 3`, qui n'autorise un saut brutal que pour les
    3 premières synchronisations après le démarrage. Passé ce cap il corrige par
    dérive lente, à quelques ppm — des jours pour rattraper une demi-heure.

    Mesuré : après une suite complète, web1 et web2 divergeaient de 1737 s (la
    durée du run), et `chronyc sources` affichait bien `-1737s` sans jamais le
    corriger. Le test qui compare les mtimes de deux hôtes pour prouver le
    séquencement des vagues (`mock-ex294`, tâche 14) échouait donc, alors que le
    lab lui-même était juste : il passait quand on le jouait seul.

    On pousse l'heure de l'HÔTE plutôt que de compter sur NTP ou le RTC, tous
    deux inopérants ici : `chronyc makestep` rend « 200 OK » sans rien corriger
    (aucune source sélectionnée, `^?`), et `hwclock -r` sort en timeout sur
    /dev/rtc0. L'hôte, lui, connaît l'heure : c'est la seule source sûre et elle
    ne dépend d'aucun réseau.

    Best-effort : un hôte injoignable ne doit pas faire échouer le reset.
    """
    cfg = _dsoxlab_ssh_config()
    if cfg is None:
        return
    for fqdn in fqdns:
        subprocess.run(
            ["ssh", "-F", str(cfg), "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
             fqdn, f"sudo -n date -s @{int(time.time())}"],
            capture_output=True,
            timeout=30,
        )


def _lab_groups_inventory(lab_root: Path) -> Path:
    """Fabrique les groupes que dsoxlab injecte au run, et les met en cache.

    Les playbooks des labs ciblent `lab_target`, `lab_<role>` et `labenv` : ce
    sont des groupes que **dsoxlab injecte au moment du run**, ils n'existent
    pas dans inventory/hosts.yml. Sans eux, `ansible-playbook -i inventory/hosts.yml`
    matche zéro hôte et sort en rc=0 : le playbook ne fait rien, et ne le dit
    pas. Un échec muet est pire qu'un échec.

    On reproduit donc les trois groupes du contrat (dsoxlab infra/inventory.py)
    et on les passe en second `-i` : Ansible fusionne les inventaires, et
    hosts.yml garde les host_vars.

    - `labenv`    : TOUS les hôtes du meta.yml.
    - `lab_target`: le seul `targets[].host` résolu.
    - `lab_<role>`: un par entrée de `roles`.
    """
    import json
    import yaml as _yaml

    lab_yaml = lab_root / "lab.yaml"
    spec = _yaml.safe_load(lab_yaml.read_text(encoding="utf-8")) or {}
    runtime = spec.get("runtime") or {}
    targets = runtime.get("targets") or []
    if not targets:
        raise RuntimeError(f"{lab_yaml} : runtime.targets vide, impossible de cibler.")

    default = runtime.get("default")
    target = next((t for t in targets if t.get("name") == default), targets[0])

    children = {"lab_target": {"hosts": {target["host"]: None}}}
    for role, fqdn in (target.get("roles") or {}).items():
        children[f"lab_{role}"] = {"hosts": {fqdn: None}}

    # labenv vient du meta.yml, pas du lab.yaml : c'est le parc complet, ce que
    # cible un setup.yaml qui prépare plusieurs machines.
    meta = _yaml.safe_load((REPO_ROOT / "meta.yml").read_text(encoding="utf-8")) or {}
    env_hosts = {
        h["name"]: None
        for h in ((meta.get("infra") or {}).get("hosts") or [])
        if h.get("name")
    }
    if env_hosts:
        children["labenv"] = {"hosts": env_hosts}

    out = REPO_ROOT / ".ansible" / "lab-groups" / f"{_lab_key(lab_root).replace('/', '_')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"all": {"children": children}}, indent=2), encoding="utf-8")
    return out


def _run_lab_playbook(playbook: Path, lab_root: Path):
    """Joue un playbook de lab avec les groupes lab_* résolus, et vérifie qu'il
    a bien touché au moins un hôte."""
    groups = _lab_groups_inventory(lab_root)
    res = _run(
        [
            "ansible-playbook",
            "-i", "inventory/hosts.yml",
            "-i", str(groups.relative_to(REPO_ROOT)),
            str(playbook.relative_to(REPO_ROOT)),
        ],
        cwd=REPO_ROOT,
    )
    # Ansible sort en rc=0 quand un pattern ne matche aucun hôte : c'est
    # exactement le silence qu'on veut casser.
    if "skipping: no hosts matched" in res.stdout or re.search(
        r"Could not match supplied host pattern", res.stdout + res.stderr
    ):
        raise RuntimeError(
            f"{playbook.relative_to(REPO_ROOT)} n'a matché AUCUN hôte.\n"
            f"Groupes fournis : {groups.relative_to(REPO_ROOT)}\n"
            "Le playbook cible-t-il bien lab_target / lab_<role> tels que "
            "déclarés dans runtime.targets[] du lab.yaml ?"
        )
    return res


def pytest_configure(config):
    """Déclare le marqueur `no_replay` (sinon pytest le refuse en --strict-markers)."""
    config.addinivalue_line(
        "markers",
        "no_replay: le module orchestre lui-même ses runs ; ne pas rejouer la "
        "solution avant ses tests.",
    )
    config.addinivalue_line(
        "markers",
        "slow: test long (redémarrage de VM). Se désélectionne avec "
        "`pytest -m 'not slow'`.",
    )


@pytest.fixture(scope="session", autouse=True)
def _snapshot_isolation_base():
    """Base les VM (base+overlay) une fois par session, sur demande explicite.

    Activé par `DSOXLAB_SNAPSHOT_ISOLATION=1` : à lancer juste après un
    `dsoxlab provision`, quand les VM sont FRAÎCHES, pour figer leur base propre.
    Idempotent : ne re-base pas une VM déjà basée. Sans cette variable, on ne
    touche pas aux disques (mais le reset par lab reste actif si les bases
    existent déjà). En mode apprenant (`LAB_NO_REPLAY=1`), aucun basing.
    """
    if (
        os.environ.get("DSOXLAB_SNAPSHOT_ISOLATION") == "1"
        and os.environ.get("LAB_NO_REPLAY") != "1"
    ):
        snapshot_base(_meta_vm_fqdns())
    yield


@pytest.fixture(scope="module", autouse=True)
def _apply_lab_state(request):
    """Joue la solution du lab avant ses tests pour garantir l'isolation.

    - Lab démo (`Makefile` + `playbook.yml` racine, pas de challenge/solution.yml) :
      lance le playbook du lab directement (`ansible-playbook playbook.yml`).
    - Lab pédagogique avec challenge Ansible (`challenge/solution.yml`) :
      lance `ansible-playbook challenge/solution.yml` (+ args si lab spécifique).
    - Lab pédagogique avec challenge Bash (`challenge/solution.sh`) ou
      sans solution Ansible : no-op (le test exécute lui-même le script).

    Si le `solution.yml`/`solution.sh` est absent, **skippe** le module avec
    un message explicite — l'apprenant doit l'écrire avant de lancer pytest.

    Activée par défaut sur tous les modules de test. Deux désactivations, à ne
    pas confondre :

    - `LAB_NO_REPLAY=1` dans l'environnement : GLOBAL et voulu. C'est le mode
      apprenant, posé par `dsoxlab check` : on note le travail de l'apprenant,
      on ne rejoue rien par-dessus.
    - `@pytest.mark.no_replay` sur le module : LOCAL, pour les rares labs qui
      s'orchestrent eux-mêmes (plusieurs runs avec des `--limit` différents,
      un playbook qu'on attend en échec…).

    Le marqueur existe parce que ces labs posaient `os.environ["LAB_NO_REPLAY"]`
    au niveau module : exécuté dès la COLLECTE, il désactivait le replay pour
    toute la session, y compris les labs collectés après. Chaque lab notait
    alors l'état laissé par son prédécesseur sur des VMs partagées. D'où des
    labs verts un par un et une section rouge en bloc, symptôme qui envoie
    chercher le bug dans les labs alors qu'il est dans leur voisin.
    """
    if os.environ.get("LAB_NO_REPLAY") == "1":
        return
    if request.node.get_closest_marker("no_replay"):
        return

    test_path = Path(str(request.fspath)).resolve()
    lab_root = _find_lab_root(test_path)
    if lab_root is None:
        return  # test hors d'un lab

    # Isolation par overlay : on reset les hôtes que CE lab utilise (lab.yaml)
    # à leur base AVANT de rejouer setup+solution. Ne reset que le nécessaire,
    # pas les 4 VM : chaque lab nettoie ses hôtes avant de les toucher, ce qui
    # suffit à l'isolation et divise le temps du run global. Le reset jette tout
    # résidu (fstab, sysctl.d, paquets, reboot) et répare même une VM bloquée au
    # boot. No-op tant que les bases n'existent pas (snapshot_base) ; opt-out par
    # DSOXLAB_SNAPSHOT_ISOLATION=0.
    if os.environ.get("DSOXLAB_SNAPSHOT_ISOLATION") != "0":
        snapshot_reset(_lab_vm_fqdns(lab_root))

    lab_name = _lab_key(lab_root)  # ex : "vault/introduction"
    challenge_yml = lab_root / "challenge" / "solution.yml"
    challenge_sh = lab_root / "challenge" / "solution.sh"
    root_playbook = lab_root / "playbook.yml"
    reference = REPO_ROOT / "solution" / lab_name / "solution.yml"

    # Lab démo : un playbook.yml livré à la racine et RIEN à résoudre. La
    # détection se faisait sur la présence d'un Makefile ; ils ont été supprimés
    # (le validator dsoxlab les interdit), donc on s'appuie sur le playbook
    # livré, qui est le vrai signal.
    #
    # L'absence de solution de référence fait partie du signal : quatre labs de
    # la section roles livrent À LA FOIS un playbook.yml (la démo du guide) et
    # un challenge. Sans ce test, ils étaient pris pour des démos et on jouait
    # la démo, pendant que les tests vérifiaient le challenge : argument-specs
    # posait 8081 côté démo quand ses tests attendaient les 8090 du challenge.
    is_demo_lab = (
        root_playbook.exists()
        and not challenge_yml.exists()
        and not challenge_sh.exists()
        and not reference.is_file()
    )

    if is_demo_lab:
        # L'état de départ était posé par `make setup` : c'est désormais le rôle
        # de setup.yaml, joué par `dsoxlab run`.
        setup_yaml = lab_root / "setup.yaml"
        if setup_yaml.exists():
            _run(
                ["ansible-playbook", "-i", "inventory/hosts.yml",
                 str(setup_yaml.relative_to(REPO_ROOT))],
                cwd=REPO_ROOT,
            )
        _run(
            ["ansible-playbook", str(root_playbook.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
        )
        return

    # Solution de référence du formateur, jouée DEPUIS solution/ sans jamais
    # être copiée dans challenge/ — c'est le modèle de linux-dsoxlab-training.
    # Elle est chiffrée : ansible-playbook la déchiffre à la volée avec
    # --vault-password-file, rien n'atterrit en clair sur le disque.
    #
    # C'est ce qui permet le contrôle « mes solutions passent mes propres
    # tests » sur les 108 labs, sans que le formateur ait à poser 108 fichiers,
    # et sans risquer de les laisser traîner dans challenge/ où l'apprenant les
    # lirait.
    vault_pass = REPO_ROOT / ".vault-pass"
    if reference.is_file() and not challenge_yml.exists():
        if not vault_pass.is_file():
            pytest.skip(
                f"[{lab_name}] solution de référence présente mais .vault-pass "
                "absent : impossible de la rejouer."
            )
        # La référence va peut-être écrire par-dessus les squelettes versionnés
        # du lab : on s'assure qu'ils seront rendus.
        _protect_lab_tree(request, lab_root)
        setup_yaml = lab_root / "setup.yaml"
        if setup_yaml.exists():
            _run_lab_playbook(setup_yaml, lab_root)
        cmd = [
            "ansible-playbook",
            "--vault-password-file", str(vault_pass.relative_to(REPO_ROOT)),
            str(reference.relative_to(REPO_ROOT)),
        ]
        cmd += _EXTRA_ARGS.get(lab_name, [])
        cmd += _INVENTORY_LABS.get(lab_name, lambda *_: [])(lab_name, lab_root)
        env = os.environ.copy()
        env.update(_roles_path(lab_root))
        env.update(_EXTRA_ENV.get(lab_name, {}))
        _run(cmd, cwd=REPO_ROOT, env=env)
        return

    # Lab shell : ses tests inspectent le script LÀ où l'apprenant l'écrit
    # (challenge/solution.sh), et pas seulement son effet. Jouer la référence
    # depuis solution/ ne suffit donc pas : il faut la poser à cet emplacement
    # le temps du module, puis l'enlever.
    #
    # Sans ça, un lab shell dont la référence existe skippait quand même : la
    # fixture ne cherchait une référence que sous forme de solution.yml.
    reference_sh = REPO_ROOT / "solution" / lab_name / "solution.sh"
    if reference_sh.is_file() and not challenge_sh.exists() and not challenge_yml.exists():
        if not vault_pass.is_file():
            pytest.skip(
                f"[{lab_name}] solution de référence présente mais .vault-pass "
                "absent : impossible de la poser."
            )
        setup_yaml = lab_root / "setup.yaml"
        if setup_yaml.exists():
            _run_lab_playbook(setup_yaml, lab_root)
        challenge_sh.parent.mkdir(parents=True, exist_ok=True)
        challenge_sh.write_text(_decrypt(reference_sh), encoding="utf-8")
        challenge_sh.chmod(0o700)
        # Finalizer plutôt que `yield` : les autres branches de cette fixture
        # font `return`, et un seul `yield` la transformerait en générateur,
        # que pytest refuserait sur ces chemins-là.
        #
        # La référence ne doit JAMAIS survivre au run : l'apprenant la lirait,
        # et le lab n'aurait plus d'objet.
        request.addfinalizer(lambda: challenge_sh.unlink(missing_ok=True))
        return

    # Lab pédagogique : challenge/solution.yml requis (écrit par l'apprenant)
    if not challenge_yml.exists() and not challenge_sh.exists():
        pytest.skip(
            f"[{lab_name}] Ni solution/{lab_name}/solution.yml (référence) ni "
            f"challenge/solution.yml (votre travail). Écrivez le vôtre en "
            f"suivant challenge/README.md, puis relancez pytest. "
            f"(Désactive cette fixture avec LAB_NO_REPLAY=1)"
        )

    # Pré-cleanup spécifique au lab (avant tout play).
    pre = _PRE_CLEANUPS.get(lab_name)
    if pre:
        _run(pre, cwd=REPO_ROOT)

    # État de départ : le setup.yaml du lab, exactement ce que joue `dsoxlab run`
    # avant de rendre la main à l'apprenant. Sans lui, un run pytest hérite de
    # l'état laissé par le lab précédent (les VMs sont partagées) et échoue, ou
    # pire, réussit à tort. C'est ce que faisaient les _PRE_CLEANUPS ad hoc, en
    # shell et lab par lab : le setup.yaml le fait déclarativement, pour tous.
    setup_yaml = lab_root / "setup.yaml"
    if setup_yaml.exists():
        _run_lab_playbook(setup_yaml, lab_root)

    if challenge_yml.exists():
        cmd = ["ansible-playbook", str(challenge_yml.relative_to(REPO_ROOT))]
        cmd += _EXTRA_ARGS.get(lab_name, [])
        cmd += _INVENTORY_LABS.get(lab_name, lambda *_: [])(lab_name, lab_root)
        env = os.environ.copy()
        env.update(_roles_path(lab_root))
        env.update(_EXTRA_ENV.get(lab_name, {}))
        _run(cmd, cwd=REPO_ROOT, env=env)
    # Si seul solution.sh existe : le test l'exécute lui-même (no-op ici).


# ----------------------------------------------------------------------
# Idempotence : la preuve que le RHCE exige, et que 106 labs sur 108
# ne demandaient pas.
# ----------------------------------------------------------------------


def lab_playbook(test_file):
    """Résout le playbook à jouer pour un lab, et les args vault qui vont avec.

    Arbitrage unique, partagé par la fixture de replay, `replay_solution()` et
    les tests qui lancent eux-mêmes ansible-playbook : le travail de
    l'apprenant (`challenge/solution.yml`) s'il existe, sinon la solution de
    référence du formateur (`solution/<lab>/solution.yml`, chiffrée).

    Un test qui code en dur `challenge/solution.yml` ne tourne QUE chez
    l'apprenant : en mode formateur ce fichier n'existe pas, et le test échoue
    sur « could not be found » sans que rien ne soit cassé.

    Args:
        test_file: __file__ du test appelant.

    Returns:
        (Path absolu du playbook, list d'args vault à passer à ansible-playbook).
        Skippe le module si aucune des deux solutions n'est jouable.
    """
    lab_root = _find_lab_root(Path(test_file))
    if lab_root is None:
        raise RuntimeError(f"Test hors d'un lab : {test_file}")
    lab_name = _lab_key(lab_root)

    playbook = lab_root / "challenge" / "solution.yml"
    if playbook.exists():
        return playbook, []

    reference = REPO_ROOT / "solution" / lab_name / "solution.yml"
    vault_pass = REPO_ROOT / ".vault-pass"
    if reference.is_file():
        if not vault_pass.is_file():
            pytest.skip(
                f"[{lab_name}] solution de référence chiffrée mais .vault-pass "
                "absent : impossible de la rejouer."
            )
        return reference, [
            "--vault-password-file", str(vault_pass.relative_to(REPO_ROOT))
        ]

    # Dernier recours : le playbook livré à la racine d'un lab démo. Il n'y a
    # rien à écrire dans ces labs, donc jamais de challenge/solution.yml ni de
    # référence : `assert_idempotent` skippait STRUCTUREL, et aucune réponse
    # d'apprenant ne pouvait lever ce skip. La fixture, elle, sait jouer ce
    # playbook depuis toujours ; ce helper l'ignorait.
    demo = lab_root / "playbook.yml"
    if demo.is_file():
        return demo, []

    pytest.skip(
        f"[{lab_name}] ni challenge/solution.yml (votre travail), ni "
        f"solution/{lab_name}/solution.yml (référence), ni playbook.yml "
        "(lab démo) : rien à rejouer."
    )


def lab_solution_text(test_file, name="solution.yml"):
    """Retourne le TEXTE de la solution du lab, déchiffré si nécessaire.

    Pour les tests qui inspectent la solution plutôt que son effet (« utilise
    bien import_tasks », « ne colle pas la passphrase en dur »). Lire
    directement la référence donnerait le chiffré : `$ANSIBLE_VAULT;1.1;AES256`
    ne contient évidemment aucun `import_tasks`, et l'assertion échouerait pour
    une raison qui n'a rien à voir avec le lab.

    Args:
        test_file: __file__ du test appelant.
        name: nom du fichier de solution (défaut : solution.yml).
    """
    lab_root = _find_lab_root(Path(test_file))
    if lab_root is None:
        raise RuntimeError(f"Test hors d'un lab : {test_file}")
    lab_name = _lab_key(lab_root)

    learner = lab_root / "challenge" / name
    if learner.exists():
        return learner.read_text(encoding="utf-8")

    reference = REPO_ROOT / "solution" / lab_name / name
    if not reference.is_file():
        pytest.skip(
            f"[{lab_name}] ni challenge/{name} (votre travail) ni "
            f"solution/{lab_name}/{name} (référence) : rien à inspecter."
        )
    return _decrypt(reference)


def lab_artifact(test_file, relpath):
    """Résout un artefact du lab : celui de l'apprenant, sinon la référence.

    Pour les tests qui vérifient un fichier ANNEXE à la solution (un fichier de
    secrets, un template, un vars_files) plutôt que la solution elle-même.

    L'artefact de l'apprenant est `challenge/<relpath>`, celui du formateur
    `solution/<lab>/<relpath>`. On rend celui qui est RÉELLEMENT en jeu, ce qui
    évite de recopier la référence dans challenge/ pour faire passer un test :
    un test qui vérifie un fichier qu'on vient d'y poser ne prouve que sa
    propre mise en place.

    Args:
        test_file: __file__ du test appelant.
        relpath: chemin relatif, ex : "files/app_secrets.yml".

    Returns:
        Path de l'artefact en jeu. Skippe le module si aucun n'existe.
    """
    lab_root = _find_lab_root(Path(test_file))
    if lab_root is None:
        raise RuntimeError(f"Test hors d'un lab : {test_file}")
    lab_name = _lab_key(lab_root)

    learner = lab_root / "challenge" / relpath
    if learner.exists():
        return learner
    reference = REPO_ROOT / "solution" / lab_name / relpath
    if reference.exists():
        return reference
    pytest.skip(
        f"[{lab_name}] ni challenge/{relpath} (votre travail) ni "
        f"solution/{lab_name}/{relpath} (référence) : rien à vérifier."
    )


def lab_script(test_file, name="solution.sh"):
    """Retourne un chemin vers un script de solution EXÉCUTABLE.

    Même arbitrage que `lab_playbook`, mais pour les labs dont la solution est
    un shell (galaxy, ansible-pull). La référence étant chiffrée, elle est
    déchiffrée dans un fichier temporaire, jamais dans le dépôt : rien ne
    traîne en clair dans challenge/, où l'apprenant le lirait.
    """
    lab_root = _find_lab_root(Path(test_file))
    if lab_root is None:
        raise RuntimeError(f"Test hors d'un lab : {test_file}")
    lab_name = _lab_key(lab_root)

    learner = lab_root / "challenge" / name
    if learner.exists():
        return learner

    reference = REPO_ROOT / "solution" / lab_name / name
    if not reference.is_file():
        pytest.skip(
            f"[{lab_name}] ni challenge/{name} (votre travail) ni "
            f"solution/{lab_name}/{name} (référence) : rien à exécuter."
        )
    text = lab_solution_text(test_file, name=name)
    tmp = Path(tempfile.mkdtemp(prefix=f"lab-{lab_name.replace('/', '-')}-"))
    script = tmp / name
    script.write_text(text, encoding="utf-8")
    script.chmod(0o700)
    return script


def replay_solution(test_file):
    """Rejoue le playbook du lab et retourne le PLAY RECAP parsé.

    Args:
        test_file: __file__ du test appelant (sert à retrouver la racine du lab).

    Returns:
        dict {hôte: {"changed": int, "failed": int, "ok": int}}.
    """
    lab_root = _find_lab_root(Path(test_file))
    lab_name = _lab_key(lab_root)
    playbook, vault_args = lab_playbook(test_file)

    cmd = ["ansible-playbook", *vault_args, str(playbook.relative_to(REPO_ROOT))]
    cmd += _EXTRA_ARGS.get(lab_name, [])
    cmd += _INVENTORY_LABS.get(lab_name, lambda *_: [])(lab_name, lab_root)
    env = os.environ.copy()
    env.update(_roles_path(lab_root))
    env.update(_EXTRA_ENV.get(lab_name, {}))
    res = _run(cmd, cwd=REPO_ROOT, env=env)

    recap = {}
    for line in res.stdout.splitlines():
        m = re.match(
            r"^(\S+)\s*:\s*ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)",
            line.strip(),
        )
        if m:
            recap[m.group(1)] = {
                "ok": int(m.group(2)),
                "changed": int(m.group(3)),
                "failed": int(m.group(5)),
            }
    if not recap:
        raise RuntimeError(
            "PLAY RECAP introuvable dans la sortie d'ansible-playbook :\n"
            f"{res.stdout[-2000:]}"
        )
    return recap


def assert_idempotent(test_file):
    """Le second passage du playbook ne doit rien changer.

    C'est LE critère du RHCE : un playbook qui rejoue et annonce encore des
    `changed` n'est pas idempotent, même si l'état final semble correct. Le
    premier passage est déjà fait (fixture `_apply_lab_state` en mode formateur,
    ou l'apprenant lui-même) : on rejoue et on exige changed=0 partout.

    Usage dans un test de lab :

        from conftest import assert_idempotent

        def test_solution_idempotente():
            assert_idempotent(__file__)
    """
    recap = replay_solution(test_file)
    drifting = {h: s["changed"] for h, s in recap.items() if s["changed"] > 0}
    assert not drifting, (
        "Le playbook n'est PAS idempotent : un second passage modifie encore "
        f"l'état ({', '.join(f'{h} → changed={c}' for h, c in drifting.items())}).\n"
        "Un playbook correct converge : au 2e run, PLAY RECAP doit afficher "
        "changed=0 partout.\n"
        "Pistes : un `command`/`shell` sans `changed_when` ni `creates`, un "
        "`lineinfile` dont la regexp ne matche pas ce qu'il vient d'écrire, ou "
        "un module qui réécrit un fichier à chaque passage."
    )
    failed = {h: s["failed"] for h, s in recap.items() if s["failed"] > 0}
    assert not failed, f"Le playbook échoue au second passage : {failed}"


# Renseigné après la définition : les labs dont l'inventaire est le livrable.
_INVENTORY_LABS["rhce/mock-ex294"] = _inventory_args
_INVENTORY_LABS["rhce/mock-ex294-2"] = _inventory_args
