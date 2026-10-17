"""Tests pytest+testinfra pour le mock RHCE EX294 #2 (lab 200).

Variante du mock #1 (rhce/mock-ex294) : mêmes catégories, valeurs différentes.
La pile est Apache (httpd) + valkey, l'utilisateur svcuser (UID 3200), le LV
lv_app en ext4 sur /srv/appdata, le port valkey 6379/tcp, le booléen
httpd_can_network_connect_db, le cron à 22h30, la collection ansible.posix.

Un test au moins par tâche, et plusieurs pour les tâches qui se ratent en
morceaux plutôt qu'en bloc : les tests regardent l'ÉTAT de la machine, jamais le
YAML.
"""

import json
import os
import re
import subprocess

import pytest
import yaml

from conftest import (
    _EXTRA_ARGS,
    REPO_ROOT,
    _roles_path,
    assert_idempotent,
    lab_host,
    lab_inventory_args,
    lab_playbook,
    lab_solution_text,
    message,
    reboot_and_wait,
    replay_solution,
)

_LAB_ROOT = REPO_ROOT / "labs" / "rhce" / "mock-ex294-2"
_LAB_KEY = "rhce/mock-ex294-2"

# Emplacements possibles du rôle web_publish de la tâche 11, dans l'ordre de
# priorité. Le challenge/README impose `roles/` à la racine du lab ; le conftest
# accepte aussi `challenge/roles/` via ANSIBLE_ROLES_PATH.
_ROLE_DIRS = (
    "roles/web_publish",
    "challenge/roles/web_publish",
)


def _role_file(relpath):
    """Retourne le YAML parsé d'un fichier du rôle web_publish, ou None.

    Même arbitrage que `lab_playbook` dans le conftest : le travail de
    l'apprenant s'il existe, sinon la solution de référence du formateur. Le
    repli sur la référence est conditionné à l'ABSENCE de
    `challenge/solution.yml`, c'est-à-dire au mode formateur.

    La référence étant chiffrée par ansible-vault, on passe par
    `lab_solution_text`, qui la déchiffre à la volée.
    """
    for role_dir in _ROLE_DIRS:
        path = _LAB_ROOT / role_dir / relpath
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if (_LAB_ROOT / "challenge" / "solution.yml").exists():
        return None  # mode apprenant : on n'inspecte que SON rôle
    reference = REPO_ROOT / "solution" / _LAB_KEY / "roles" / "web_publish"
    if not (reference / relpath).is_file():
        return None
    return yaml.safe_load(
        lab_solution_text(__file__, name=f"roles/web_publish/{relpath}")
    ) or []


def _lancer_solution(*args_supplementaires):
    """Lance le playbook du lab, en autorisant des arguments en plus.

    `replay_solution` ne sait pas passer `--tags`, et ne rend que ok/changed/
    failed : ni `rescued`, ni `ignored`. Or ce sont les compteurs qui prouvent la
    tâche 13, et `--tags` est le seul moyen de prouver la tâche 17 sans lire le
    YAML.

    On reconstruit ici la même commande que le conftest, sans le modifier.
    """
    playbook, args_vault = lab_playbook(__file__)
    cmd = ["ansible-playbook", *args_vault, str(playbook.relative_to(REPO_ROOT))]
    cmd += _EXTRA_ARGS[_LAB_KEY]
    cmd += lab_inventory_args(__file__)
    cmd += list(args_supplementaires)
    env = os.environ.copy()
    env.update(_roles_path(_LAB_ROOT))
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env, check=False)


def _recap_de(sortie, hote):
    """Extrait les compteurs du PLAY RECAP pour un hôte donné."""
    for ligne in sortie.splitlines():
        if not ligne.strip().startswith(f"{hote} "):
            continue
        compteurs = dict(re.findall(r"(\w+)=(\d+)", ligne))
        if "ok" in compteurs and "failed" in compteurs:
            return {cle: int(valeur) for cle, valeur in compteurs.items()}
    raise AssertionError(
        f"Aucune ligne de PLAY RECAP pour {hote} dans la sortie :\n"
        f"{sortie[-2000:]}"
    )


def _facts_locaux(hote):
    """Facts `ansible_local` REMONTÉS par une collecte réelle sur un hôte.

    On n'inspecte pas le fichier .fact : on demande à Ansible ce qu'il voit. Un
    .fact présent mais mal formé, mal nommé, ou posé en 0755 (donc exécuté au
    lieu d'être lu) ne remonte pas, et c'est tout ce qui compte.
    """
    res = subprocess.run(
        ["ansible", *lab_inventory_args(__file__), hote,
         "-m", "ansible.builtin.setup", "-a", "filter=ansible_local"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, message(
        en=f"Gathering facts failed on {hote}:\n"
        f"--- stdout ---\n{res.stdout.strip()}\n"
        f"--- stderr ---\n{res.stderr.strip()}",
        fr=f"La collecte de facts a échoué sur {hote} :\n"
        f"--- stdout ---\n{res.stdout.strip()}\n"
        f"--- stderr ---\n{res.stderr.strip()}",
    )
    _, _, corps = res.stdout.partition("=>")
    assert corps.strip(), message(
        en=f"Unexpected output from the fact gathering on {hote}:\n{res.stdout}",
        fr=f"Sortie inattendue de la collecte sur {hote} :\n{res.stdout}",
    )
    return json.loads(corps)["ansible_facts"].get("ansible_local", {})


@pytest.fixture(scope="module")
def web1():
    return lab_host("web1.lab")


@pytest.fixture(scope="module")
def web2():
    return lab_host("web2.lab")


@pytest.fixture(scope="module")
def db1():
    return lab_host("db1.lab")


# ─── Tâche 1 : Inventaire ─────────────────────────────────────────────────
def test_01_inventory_groups(db1, web1):
    """L'inventaire doit déclarer les deux groupes ET joindre leurs hôtes."""
    graph = subprocess.run(
        ["ansible-inventory", *lab_inventory_args(__file__), "--graph"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert graph.returncode == 0, message(
        en="ansible-inventory could not read the lab's inventory:\n"
        f"{graph.stderr.strip()}",
        fr="ansible-inventory n'a pas su lire l'inventaire du lab :\n"
        f"{graph.stderr.strip()}",
    )
    out = graph.stdout
    for group, members in (
        ("frontends", ("web1.lab", "web2.lab")),
        ("backends", ("db1.lab",)),
    ):
        assert f"@{group}:" in out, message(
            en=f"Group {group} absent from the inventory.\nSeen:\n{out.strip()}",
            fr=f"Groupe {group} absent de l'inventaire.\nVu :\n{out.strip()}",
        )
        section = out.split(f"@{group}:", 1)[1].split("@", 1)[0]
        for member in members:
            assert member in section, message(
                en=f"{member} must belong to the {group} group.\n"
                f"Seen:\n{out.strip()}",
                fr=f"{member} doit appartenir au groupe {group}.\n"
                f"Vu :\n{out.strip()}",
            )

    ping = subprocess.run(
        ["ansible", *lab_inventory_args(__file__), "all",
         "-m", "ansible.builtin.ping"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ping.returncode == 0, message(
        en="All 3 hosts must answer the Ansible ping through YOUR inventory.\n"
        f"--- stdout ---\n{ping.stdout.strip()}\n"
        f"--- stderr ---\n{ping.stderr.strip()}",
        fr="Les 3 hôtes doivent répondre au ping Ansible à travers VOTRE "
        f"inventaire.\n--- stdout ---\n{ping.stdout.strip()}\n"
        f"--- stderr ---\n{ping.stderr.strip()}",
    )
    assert ping.stdout.count('"ping": "pong"') == 3, message(
        en="3 'pong' expected (web1, web2, db1).\n"
        f"--- stdout ---\n{ping.stdout.strip()}",
        fr="3 'pong' attendus (web1, web2, db1).\n"
        f"--- stdout ---\n{ping.stdout.strip()}",
    )


# ─── Tâche 2 — Variables (vérifié sur un fichier produit par le playbook) ──
def test_02_variables_precedence(web1):
    """Tâche 2 : group_vars + host_vars correctement résolus."""
    f = web1.file("/tmp/lab200-vars.txt")
    assert f.exists, message(
        en="The playbook must drop /tmp/lab200-vars.txt on web1",
        fr="Le playbook doit déposer /tmp/lab200-vars.txt sur web1",
    )
    content = f.content_string
    assert "staging" in content, message(
        en="deploy_stage must be 'staging'",
        fr="deploy_stage doit valoir 'staging'",
    )
    assert "pool_size: 8" in content or "pool_size = 8" in content, message(
        en="pool_size must be 8. It is a group variable, and the brief fixes "
           "its value: a host variable must not override it here.",
        fr="pool_size doit valoir 8. C'est une variable de groupe, et "
           "l'énoncé en fixe la valeur : une variable d'hôte ne doit pas la "
           "surcharger ici.",
    )


# ─── Tâche 3 — Vault ─────────────────────────────────────────────────────
def test_03_vault_decrypted(db1):
    f = db1.file("/tmp/lab200-token.txt")
    assert f.exists, message(
        en="/tmp/lab200-token.txt missing: vars_files vault.yml did not work",
        fr="/tmp/lab200-token.txt absent — vars_files vault.yml KO",
    )
    assert f.mode == 0o600, message(
        en=f"Expected mode 0600, seen: {oct(f.mode)}",
        fr=f"Mode attendu 0600, vu : {oct(f.mode)}",
    )
    assert "Ex294-Deux" in f.content_string, message(
        en="api_token was expected, decrypted",
        fr="api_token déchiffré attendu",
    )


# ─── Tâche 4 — Templates et fichiers ────────────────────────────────────
def test_04_template_service_conf(db1):
    f = db1.file("/tmp/lab200-service.conf")
    assert f.exists, message(
        en="/tmp/lab200-service.conf is missing: the template was not "
           "rendered on db1 (task 4).",
        fr="/tmp/lab200-service.conf est absent : le template n'a pas été "
           "rendu sur db1 (tâche 4).",
    )
    assert f.mode == 0o600, message(
        en=f"Expected mode 0600, seen: {oct(f.mode)}",
        fr=f"Mode attendu 0600, vu : {oct(f.mode)}",
    )
    assert f.user == "svcuser", message(
        en=f"/tmp/lab200-service.conf belongs to {f.user}, expected svcuser. "
           f"The account must exist before the template is rendered.",
        fr=f"/tmp/lab200-service.conf appartient à {f.user}, attendu "
           f"svcuser. Le compte doit exister avant que le template ne soit "
           f"rendu.",
    )
    assert f.group == "svcgroup", message(
        en=f"/tmp/lab200-service.conf has group {f.group}, expected "
           f"svcgroup. owner: does not set the group: group: is needed too.",
        fr=f"/tmp/lab200-service.conf a le groupe {f.group}, attendu "
           f"svcgroup. owner: ne pose pas le groupe : il faut aussi group:.",
    )
    content = f.content_string
    assert "lab200schema" in content, message(
        en="schema_name must appear",
        fr="schema_name doit apparaître",
    )
    # Le rendu doit contenir le nom d'hôte Ansible (« db1 » sur db1.lab), preuve
    # qu'il est rendu PAR HÔTE et non figé.
    assert re.search(r"\bdb1\b", content), message(
        en="The rendering of /tmp/lab200-service.conf must contain the Ansible host "
        f"name (« db1 » on db1.lab), absent from the contents:\n{content.strip()[:200]}\n"
        "Without it, this is not a template rendered per host.",
        fr="Le rendu de /tmp/lab200-service.conf doit contenir le nom d'hôte Ansible "
        f"(« db1 » sur db1.lab), absent du contenu :\n{content.strip()[:200]}\n"
        "Sans lui, ce n'est pas un template rendu par hôte.",
    )


# ─── Tâche 5 — Paquets ──────────────────────────────────────────────────
def test_05_packages_installed(db1, web1, web2):
    assert db1.package("httpd").is_installed, message(
        en="httpd is not installed on db1 (task 5).",
        fr="httpd n'est pas installé sur db1 (tâche 5).",
    )
    assert db1.package("valkey").is_installed, message(
        en="valkey is not installed on db1 (task 5).",
        fr="valkey n'est pas installé sur db1 (tâche 5).",
    )
    assert db1.package("python3-libselinux").is_installed, message(
        en="python3-libselinux is not installed on db1. It provides the "
           "Python bindings the SELinux modules need: without it, task 8 "
           "fails on an import nobody expects.",
        fr="python3-libselinux n'est pas installé sur db1. Il fournit les "
           "liaisons Python dont les modules SELinux ont besoin : sans lui, "
           "la tâche 8 échoue sur un import que personne n'attend.",
    )
    # python3-libselinux est exigé « sur TOUS les hôtes » : sur les frontends,
    # c'est ce paquet qui fournit les liaisons Python dont
    # ansible.posix.seboolean a besoin (tâche 8).
    for host, nom in ((web1, "web1"), (web2, "web2")):
        assert host.package("python3-libselinux").is_installed, message(
            en=f"python3-libselinux must be installed on {nom}.lab: the brief "
            "requires it on every host.",
            fr=f"python3-libselinux doit être installé sur {nom}.lab : l'énoncé "
            "l'exige sur tous les hôtes.",
        )


# ─── Tâche 6 — Services ─────────────────────────────────────────────────
def test_06_services_running(web1, db1):
    assert web1.service("httpd").is_running, message(
        en="httpd is not working on web1",
        fr="httpd KO sur web1",
    )
    assert web1.service("httpd").is_enabled, message(
        en="httpd runs on web1 but is not enabled at boot: state: started and "
           "enabled: true are two distinct options, and only the second "
           "survives a restart.",
        fr="httpd tourne sur web1 mais n'est pas activé au démarrage : "
           "state: started et enabled: true sont deux options distinctes, et "
           "seule la seconde survit à un redémarrage.",
    )
    assert db1.service("valkey").is_running, message(
        en="valkey is not working on db1",
        fr="valkey KO sur db1",
    )
    # « démarrés ET activés au boot » : les deux moitiés de l'exigence sont
    # testées, pour httpd comme pour valkey.
    assert db1.service("valkey").is_enabled, message(
        en="valkey runs on db1 but is not enabled at boot: it would not come back "
        "after a restart (task 6).",
        fr="valkey tourne sur db1 mais n'est pas activé au boot : il ne reviendrait "
        "pas après un redémarrage (tâche 6).",
    )


# ─── Tâche 7 — Utilisateurs ─────────────────────────────────────────────
def test_07_user_svcuser(db1):
    user = db1.user("svcuser")
    assert user.exists, message(
        en="The svcuser account does not exist on db1 (task 7).",
        fr="Le compte svcuser n'existe pas sur db1 (tâche 7).",
    )
    assert user.uid == 3200, message(
        en=f"svcuser's UID is {user.uid}, expected 3200. Without uid:, the "
           f"system picks the next free one, which is never the same twice.",
        fr=f"L'UID de svcuser est {user.uid}, attendu 3200. Sans uid:, le "
           f"système prend le premier libre, qui n'est jamais le même deux "
           f"fois.",
    )
    assert user.group == "svcgroup", message(
        en=f"svcuser's primary group is {user.group}, expected svcgroup. The "
           f"group must exist before the account that takes it.",
        fr=f"Le groupe primaire de svcuser est {user.group}, attendu "
           f"svcgroup. Le groupe doit exister avant le compte qui le prend.",
    )
    assert user.shell == "/bin/bash", message(
        en=f"svcuser must have the /bin/bash shell (task 7), seen: {user.shell!r}.",
        fr=f"svcuser doit avoir le shell /bin/bash (tâche 7), vu : {user.shell!r}.",
    )
    grp = db1.group("svcgroup")
    assert grp.exists, message(
        en="The svcgroup group does not exist on db1 (task 7).",
        fr="Le groupe svcgroup n'existe pas sur db1 (tâche 7).",
    )
    assert grp.gid == 3200, message(
        en=f"svcgroup's GID is {grp.gid}, expected 3200. Like the UID, it is "
           f"fixed by the brief so that file ownership is predictable.",
        fr=f"Le GID de svcgroup est {grp.gid}, attendu 3200. Comme l'UID, il "
           f"est fixé par l'énoncé pour que la propriété des fichiers soit "
           f"prévisible.",
    )


def test_07b_svcuser_sudo_journalctl_nopasswd(db1):
    """svcuser doit lancer journalctl en sudo SANS mot de passe, et RIEN d'autre.

    L'énoncé l'exige explicitement (« uniquement cette commande »). On interroge
    la politique sudo effective plutôt que le fichier : c'est l'état réel qui
    compte, peu importe où la règle est écrite.
    """
    allowed = db1.run("sudo -l -U svcuser 2>/dev/null")
    assert allowed.rc == 0, message(
        en="Could not read svcuser's sudo policy (sudo -l -U svcuser).",
        fr="Impossible de lire la politique sudo de svcuser (sudo -l -U svcuser).",
    )
    out = allowed.stdout
    assert "NOPASSWD" in out and "/usr/bin/journalctl" in out, message(
        en="svcuser must be able to run /usr/bin/journalctl through sudo without a "
        f"password.\nPolicy seen:\n{out.strip()}\n"
        "Declare the rule in /etc/sudoers.d/ (validated by visudo -cf).",
        fr="svcuser doit pouvoir exécuter /usr/bin/journalctl en sudo sans mot de "
        f"passe.\nPolitique vue :\n{out.strip()}\n"
        "Déclarez la règle dans /etc/sudoers.d/ (validée par visudo -cf).",
    )
    # « uniquement cette commande » : un blanc-seing est une faute de sécurité.
    assert not re.search(r"NOPASSWD:\s*ALL\b", out), message(
        en="svcuser has NOPASSWD sudo on EVERY command.\n"
        f"Policy seen:\n{out.strip()}\n"
        "The brief asks for /usr/bin/journalctl only: narrow the rule.",
        fr="svcuser a un sudo NOPASSWD sur TOUTES les commandes.\n"
        f"Politique vue :\n{out.strip()}\n"
        "L'énoncé demande uniquement /usr/bin/journalctl : restreignez la règle.",
    )


# ─── Tâche 8 — SELinux ──────────────────────────────────────────────────
def test_08_selinux_httpd_can_network_connect_db(web1):
    """Le booléen doit être actif dans le noyau, ici et maintenant."""
    cmd = web1.run("getsebool httpd_can_network_connect_db")
    assert cmd.rc == 0, message(
        en=f"getsebool failed: {cmd.stderr.strip()}",
        fr=f"getsebool a échoué : {cmd.stderr.strip()}",
    )
    value = cmd.stdout.rsplit("-->", 1)[-1].strip()
    assert value == "on", message(
        en=f"httpd_can_network_connect_db must be on, seen: {value or '?'}\n"
        f"Full output: {cmd.stdout.strip()}",
        fr=f"httpd_can_network_connect_db doit être activé, vu : {value or '?'}\n"
        f"Sortie complète : {cmd.stdout.strip()}",
    )


def test_08b_selinux_boolean_persistent(web1):
    """Le booléen doit survivre au reboot (SELinux : valeur « persistent »).

    `setsebool` sans -P ne tient que jusqu'au redémarrage : c'est l'erreur
    classique qui fait perdre les points à l'examen.
    """
    cmd = web1.run("semanage boolean -l | grep '^httpd_can_network_connect_db'")
    assert cmd.rc == 0, message(
        en="Could not read the boolean's persistent value "
        "(semanage boolean -l).",
        fr="Impossible de lire la valeur persistante du booléen "
        "(semanage boolean -l).",
    )
    assert re.search(r"\(\s*on\s*,\s*on\s*\)", cmd.stdout), message(
        en="httpd_can_network_connect_db must be enabled PERSISTENTLY.\n"
        f"Seen: {cmd.stdout.strip()}\n"
        "The second field is the value at next boot: it must be « on ». "
        "The ansible.posix.seboolean module has a parameter for that.",
        fr="httpd_can_network_connect_db doit être activé DE FAÇON PERSISTANTE.\n"
        f"Vu : {cmd.stdout.strip()}\n"
        "Le second champ est la valeur au prochain boot : elle doit être « on ». "
        "Le module ansible.posix.seboolean prend un paramètre pour cela.",
    )


# ─── Tâche 9 — Firewalld ────────────────────────────────────────────────
def test_09_firewall_http_https_open(web1):
    cmd = web1.run("firewall-cmd --list-services")
    assert "http" in cmd.stdout, message(
        en=f"The http service is not open on web1 (seen: {cmd.stdout.strip()}).",
        fr=f"Le service http n'est pas ouvert sur web1 (vu : "
           f"{cmd.stdout.strip()}).",
    )
    assert "https" in cmd.stdout, message(
        en=f"The https service is not open on web1 (seen: {cmd.stdout.strip()}). "
           f"Both services go in the same firewalld task, as a list.",
        fr=f"Le service https n'est pas ouvert sur web1 (vu : "
           f"{cmd.stdout.strip()}). Les deux services vont dans la même tâche "
           f"firewalld, sous forme de liste.",
    )


def test_09b_firewall_valkey_port_db1(db1):
    cmd = db1.run("firewall-cmd --list-ports")
    assert "6379/tcp" in cmd.stdout, message(
        en="Port 6379/tcp (valkey) must be open on db1 (seen: "
        f"{cmd.stdout.strip()}).",
        fr="Le port 6379/tcp (valkey) doit être ouvert sur db1 (vu : "
        f"{cmd.stdout.strip()}).",
    )


def test_09c_firewall_rules_are_permanent(web1, db1):
    """Les règles doivent être dans la configuration PERMANENTE, pas seulement
    dans le runtime.

    `firewall-cmd --add-service=http` sans --permanent est perdu au reboot.
    `--list-services`/`--list-ports` seul ne voit que le runtime.
    """
    out = web1.run("firewall-cmd --permanent --list-services")
    for svc in ("http", "https"):
        assert svc in out.stdout, message(
            en=f"The {svc} service must be opened PERMANENTLY on web1 "
            f"(seen as permanent: {out.stdout.strip()}).\n"
            "A runtime rule disappears at restart.",
            fr=f"Le service {svc} doit être ouvert de façon PERMANENTE sur web1 "
            f"(vu en permanent : {out.stdout.strip()}).\n"
            "Une règle runtime disparaît au redémarrage.",
        )
    out = db1.run("firewall-cmd --permanent --list-ports")
    assert "6379/tcp" in out.stdout, message(
        en="Port 6379/tcp must be open PERMANENTLY on db1 "
        f"(seen as permanent: {out.stdout.strip()}).",
        fr="Le port 6379/tcp doit être ouvert de façon PERMANENTE sur db1 "
        f"(vu en permanent : {out.stdout.strip()}).",
    )


# ─── Tâche 10 — Stockage ────────────────────────────────────────────────
def test_10_lvm_ext4_mounted(db1):
    mount = db1.mount_point("/srv/appdata")
    assert mount.exists, message(
        en="/srv/appdata must be mounted",
        fr="/srv/appdata doit être monté",
    )
    assert mount.filesystem == "ext4", message(
        en=f"/srv/appdata carries a {mount.filesystem} filesystem, expected "
           f"ext4. The logical volume must be formatted before being mounted.",
        fr=f"/srv/appdata porte un système de fichiers {mount.filesystem}, "
           f"attendu ext4. Le volume logique doit être formaté avant d'être "
           f"monté.",
    )


def test_10b_mount_persistent_fstab(db1):
    """Le montage doit être déclaré dans /etc/fstab (persistance reboot)."""
    fstab = db1.file("/etc/fstab").content_string
    line = next(
        (
            ln for ln in fstab.splitlines()
            if not ln.lstrip().startswith("#") and " /srv/appdata " in f" {ln} "
        ),
        None,
    )
    assert line is not None, message(
        en="No active /srv/appdata entry in /etc/fstab: the mount will not "
        "survive a reboot.\n"
        "The ansible.posix.mount module writes to fstab with state=mounted.",
        fr="Aucune entrée /srv/appdata active dans /etc/fstab : le montage ne "
        "survivra pas au reboot.\n"
        "Le module ansible.posix.mount écrit dans fstab avec state=mounted.",
    )
    assert "ext4" in line, message(
        en=f"The fstab entry for /srv/appdata must be ext4 (seen: {line.strip()}).",
        fr=f"L'entrée fstab de /srv/appdata doit être en ext4 (vu : {line.strip()}).",
    )


def test_10c_lv_app_nom_et_taille(db1):
    """Le volume logique doit s'appeler lv_app et faire ~400 Mo (tâche 10).

    Un LV nommé autrement, ou dimensionné à 100 Mo au lieu de 400, monterait
    aussi bien. L'énoncé impose le nom exact `lv_app` et la taille 400 Mo. La
    taille est arrondie au multiple d'extents (4 Mo), d'où une tolérance.
    """
    res = db1.run(
        "lvs --noheadings --nosuffix --units m -o lv_name,lv_size vg_lab"
    )
    assert res.rc == 0, message(
        en=f"Could not list the LVs of the vg_lab VG on db1: {res.stderr.strip()}",
        fr=f"Impossible de lister les LV du VG vg_lab sur db1 : {res.stderr.strip()}",
    )
    tailles = {}
    for ligne in res.stdout.strip().splitlines():
        champs = ligne.split()
        if len(champs) >= 2:
            try:
                tailles[champs[0]] = float(champs[1])
            except ValueError:
                continue
    assert "lv_app" in tailles, message(
        en=f"No LV named « lv_app » in vg_lab (seen: {sorted(tailles) or 'none'}).\n"
        "The brief imposes that exact name.",
        fr=f"Aucun LV nommé « lv_app » dans vg_lab (vus : {sorted(tailles) or 'aucun'}).\n"
        "L'énoncé impose ce nom exact.",
    )
    taille = tailles["lv_app"]
    assert abs(taille - 400.0) <= 16.0, message(
        en=f"lv_app must be about 400 MB, measured: {taille:.0f} MB.\n"
        "The size is a criterion of task 10, just like the mount.",
        fr=f"lv_app doit faire ~400 Mo, mesuré : {taille:.0f} Mo.\n"
        "La taille est un critère de la tâche 10, au même titre que le montage.",
    )


# ─── Tâche 11 — Rôle web_publish ────────────────────────────────────────
def test_11_role_index_html(web1, web2):
    for host in (web1, web2):
        f = host.file("/var/www/html/index.html")
        assert f.exists, message(
            en=f"index.html missing on {host.system_info.hostname}",
            fr=f"index.html absent sur {host.system_info.hostname}",
        )


def test_11b_template_contient_le_hostname(web1, web2):
    """Le template doit produire un contenu PAR HÔTE, pas un fichier statique."""
    for host, name in ((web1, "web1"), (web2, "web2")):
        content = host.file("/var/www/html/index.html").content_string
        assert name in content, message(
            en=f"index.html on {name}.lab does not contain its inventory host "
            f"name.\nContents: {content.strip()[:200]}\n"
            "The template must be rendered per host (inventory_hostname).",
            fr=f"index.html sur {name}.lab ne contient pas son nom d'hôte "
            f"d'inventaire.\nContenu : {content.strip()[:200]}\n"
            "Le template doit être rendu par hôte (inventory_hostname).",
        )


def test_11c_role_declare_un_handler(web1):
    """Le rôle doit déclarer un handler notifié par la tâche de template.

    Un handler qui n'est jamais notifié ne laisse aucune trace dans l'état final,
    donc testinfra ne peut pas le voir. On contrôle donc la STRUCTURE du rôle.
    """
    handlers = _role_file("handlers/main.yml")
    if handlers is None:
        handlers = _role_file("handlers/main.yaml")
    assert handlers is not None, message(
        en="The web_publish role must declare a handler in "
        "labs/rhce/mock-ex294-2/roles/web_publish/handlers/main.yml (missing).",
        fr="Le rôle web_publish doit déclarer un handler dans "
        "labs/rhce/mock-ex294-2/roles/web_publish/handlers/main.yml (absent).",
    )
    names = {h.get("name", "") for h in handlers if isinstance(h, dict)}
    assert any("httpd" in n.lower() for n in names), message(
        en="No handler about httpd in the web_publish role "
        f"(handlers seen: {sorted(names) or 'none'}).",
        fr="Aucun handler concernant httpd dans le rôle web_publish "
        f"(handlers vus : {sorted(names) or 'aucun'}).",
    )

    tasks = _role_file("tasks/main.yml")
    if tasks is None:
        tasks = _role_file("tasks/main.yaml")
    assert tasks is not None, message(
        en="The web_publish role must have tasks/main.yml.",
        fr="Le rôle web_publish doit avoir tasks/main.yml.",
    )
    notifying = [
        t for t in tasks
        if isinstance(t, dict) and t.get("notify")
        and any(k.endswith("template") for k in t)
    ]
    assert notifying, message(
        en="The task that deploys the template must notify the handler (the "
        "`notify:` keyword). Without a notification the handler never runs, and "
        "httpd never re-reads its configuration.",
        fr="La tâche qui déploie le template doit notifier le handler "
        "(mot-clé `notify:`). Sans notification, le handler ne tourne jamais et "
        "httpd ne relit pas sa configuration.",
    )


# ─── Tâche 12 — Conditions et boucles ───────────────────────────────────
def test_12_loop_6_files_parity(db1):
    """Les 6 fichiers doivent porter LEUR parité."""
    expected = {
        1: "odd",
        2: "even",
        3: "odd",
        4: "even",
        5: "odd",
        6: "even",
    }
    for n, parity in expected.items():
        f = db1.file(f"/tmp/slot{n}")
        assert f.exists, message(
            en=f"/tmp/slot{n} missing",
            fr=f"/tmp/slot{n} absent",
        )
        content = f.content_string
        assert re.search(rf"\b{parity}\b", content), message(
            en=f"/tmp/slot{n} must contain the word '{parity}', seen: "
            f"{content.strip()[:50]!r}\n"
            "The parity condition must be about the file's number.",
            fr=f"/tmp/slot{n} doit contenir le mot '{parity}', vu : "
            f"{content.strip()[:50]!r}\n"
            "La condition de parité doit porter sur le numéro du fichier.",
        )


def _aplatir_taches(taches):
    """Déplie récursivement une liste de tâches (block/rescue/always compris)."""
    for t in taches or []:
        if not isinstance(t, dict):
            continue
        if "block" in t:
            yield from _aplatir_taches(t.get("block"))
            yield from _aplatir_taches(t.get("rescue"))
            yield from _aplatir_taches(t.get("always"))
        else:
            yield t


def test_12b_les_six_fichiers_en_une_seule_tache():
    """L'énoncé impose que les 6 fichiers de parité tiennent en UNE tâche.

    C'est une contrainte de STRUCTURE, invisible dans l'état final : six `copy:`
    séparés produiraient les mêmes /tmp/slotN. On la vérifie sur la solution
    effectivement jouée, comme les autres contrôles structurels.
    """
    plays = yaml.safe_load(lab_solution_text(__file__)) or []
    motif = re.compile(r"/tmp/slot(\d|\{\{)")
    cibles = []
    for play in plays:
        if not isinstance(play, dict):
            continue
        for tache in _aplatir_taches(play.get("tasks")):
            for val in tache.values():
                if isinstance(val, dict):
                    dest = str(val.get("dest") or val.get("path") or "")
                    if motif.search(dest):
                        cibles.append(tache)
                        break
    assert len(cibles) == 1, message(
        en=f"Task 12 must create /tmp/slot1..6 in ONE SINGLE task (with a loop), "
        f"but {len(cibles)} task(s) create those files.\n"
        "Six separate tasks produce the same state but break the brief.",
        fr=f"La tâche 12 doit créer /tmp/slot1..6 en UNE SEULE tâche (avec une "
        f"boucle), or {len(cibles)} tâche(s) créent ces fichiers.\n"
        "Six tâches séparées produisent le même état mais violent l'énoncé.",
    )
    unique = cibles[0]
    assert any(cle in unique for cle in ("loop", "with_items", "with_sequence")), message(
        en="The task that creates the 6 files must carry a loop (`loop:`).\n"
        f"Keys of the task seen: {sorted(unique)}",
        fr="La tâche qui crée les 6 fichiers doit porter une boucle (`loop:`).\n"
        f"Clés de la tâche vue : {sorted(unique)}",
    )


# ─── Tâche 13 — block / rescue / always ─────────────────────────────────
@pytest.fixture(scope="module")
def run_complet():
    """Un run complet du playbook, dont on garde la sortie brute.

    Le PLAY RECAP est le seul endroit où l'on peut lire `rescued` et `ignored`.
    """
    res = _lancer_solution()
    assert res.returncode == 0, message(
        en="The playbook must end in success: a rescue that catches an error "
        "yields a zero return code.\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}",
        fr="Le playbook doit se terminer en succès : un rescue qui rattrape une "
        "erreur rend un rc nul.\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}",
    )
    return res.stdout


def test_13_le_rescue_a_vraiment_rattrape_un_echec(run_complet):
    """Prouve le rescue par les compteurs du PLAY RECAP, pas par le YAML."""
    recap = _recap_de(run_complet, "db1.lab")
    assert recap.get("rescued", 0) >= 1, message(
        en="No rescue fired on db1 (rescued="
        f"{recap.get('rescued', 0)}).\n"
        "The task inside the block must fail FOR REAL and the rescue must "
        "catch it.\n"
        f"RECAP db1: {recap}",
        fr="Aucun rescue n'a été déclenché sur db1 (rescued="
        f"{recap.get('rescued', 0)}).\n"
        "La tâche du block doit échouer POUR DE VRAI et le rescue doit la "
        "rattraper.\n"
        f"RECAP db1 : {recap}",
    )
    assert recap.get("ignored", 0) == 0, message(
        en=f"db1 reports ignored={recap.get('ignored')}: an error was swept under "
        "the carpet with `ignore_errors` instead of being handled by a "
        "`rescue`.\n"
        f"RECAP db1: {recap}",
        fr=f"db1 rapporte ignored={recap.get('ignored')} : une erreur a été mise "
        "sous le tapis avec `ignore_errors` au lieu d'être traitée par un "
        "`rescue`.\n"
        f"RECAP db1 : {recap}",
    )
    assert recap["failed"] == 0, message(
        en=f"The play must carry on despite the incident (failed={recap['failed']}).\n"
        f"RECAP db1: {recap}",
        fr=f"Le play doit se poursuivre malgré l'incident (failed={recap['failed']}).\n"
        f"RECAP db1 : {recap}",
    )


def test_13b_le_rescue_et_le_always_ont_laisse_leurs_traces(db1):
    """Les deux marqueurs du bloc, et l'identité de la tâche qui a échoué.

    Le contenu attendu est le nom exact imposé par l'énoncé à la tâche qui
    échoue. Il se lit dans `ansible_failed_task`, une variable qui n'EXISTE que
    dans un `rescue`.
    """
    incident = db1.file("/tmp/lab200-incident.txt")
    assert incident.exists, message(
        en="/tmp/lab200-incident.txt missing: the rescue did not record the incident.",
        fr="/tmp/lab200-incident.txt absent : le rescue n'a pas consigné l'incident.",
    )
    assert incident.mode == 0o644, message(
        en=f"Expected mode 0644, seen: {oct(incident.mode)}",
        fr=f"Mode attendu 0644, vu : {oct(incident.mode)}",
    )
    lignes = [ln.strip() for ln in incident.content_string.splitlines() if ln.strip()]
    assert "Lancer l'agent lab200" in lignes, message(
        en="/tmp/lab200-incident.txt must contain the name of the task that failed, "
        "as Ansible reports it, on a line of its own.\n"
        f"Lines seen: {lignes}\n"
        "The variable that carries it exists only inside a `rescue`.",
        fr="/tmp/lab200-incident.txt doit contenir le nom de la tâche qui a échoué, "
        "tel qu'Ansible le rapporte, sur une ligne à lui.\n"
        f"Lignes vues : {lignes}\n"
        "La variable qui le porte n'est disponible que dans un `rescue`.",
    )

    fin = db1.file("/tmp/lab200-incident-fin.txt")
    assert fin.exists, message(
        en="/tmp/lab200-incident-fin.txt missing: the section that must run in "
        "EVERY case did not, although the block had just failed.",
        fr="/tmp/lab200-incident-fin.txt absent : la section qui doit s'exécuter "
        "dans TOUS les cas ne l'a pas fait, alors que le bloc a justement échoué.",
    )
    assert fin.mode == 0o644, message(
        en=f"Expected mode 0644, seen: {oct(fin.mode)}",
        fr=f"Mode attendu 0644, vu : {oct(fin.mode)}",
    )


# ─── Tâche 14 — Déploiement par vagues (serial) ─────────────────────────
def test_14_les_vagues_sont_reellement_sequencees(web1, web2):
    """Prouve `serial` par les horodatages de l'état posé, pas par le YAML.

    Avec `serial: 1` et une stabilisation de 6 secondes, web1 est traité, on
    attend, puis web2. Sans séquencement, les deux copies partent dans le même
    lot et les mtimes tombent à quelques millisecondes l'un de l'autre.
    """
    f1 = web1.file("/tmp/lab200-palier-web1.lab.txt")
    f2 = web2.file("/tmp/lab200-palier-web2.lab.txt")
    assert f1.exists, message(
        en="/tmp/lab200-palier-web1.lab.txt missing on web1",
        fr="/tmp/lab200-palier-web1.lab.txt absent sur web1",
    )
    assert f2.exists, message(
        en="/tmp/lab200-palier-web2.lab.txt missing on web2",
        fr="/tmp/lab200-palier-web2.lab.txt absent sur web2",
    )

    for f, nom in ((f1, "web1"), (f2, "web2")):
        assert f.mode == 0o644, message(
            en=f"The stage marker of {nom} must be 0644 (task 14), seen: "
            f"{oct(f.mode)}.",
            fr=f"Le marqueur de palier de {nom} doit être en 0644 (tâche 14), vu : "
            f"{oct(f.mode)}.",
        )
        assert f.user == "root", message(
            en=f"The stage marker of {nom} must belong to root (task 14), "
            f"seen: {f.user}.",
            fr=f"Le marqueur de palier de {nom} doit appartenir à root (tâche 14), "
            f"vu : {f.user}.",
        )

    # Décalage d'horloge entre les deux VMs, encadré.
    avant = float(web1.check_output("date +%s.%N"))
    milieu = float(web2.check_output("date +%s.%N"))
    apres = float(web1.check_output("date +%s.%N"))
    decalage = milieu - (avant + apres) / 2
    assert abs(decalage) < 1.0, message(
        en=f"The clocks of web1 and web2 differ by {decalage:.2f} s: the proof of "
        "sequencing rests on comparing their mtimes. Check chronyd on both "
        "VMs.",
        fr=f"Les horloges de web1 et web2 divergent de {decalage:.2f} s : la preuve "
        "du séquencement repose sur la comparaison de leurs mtimes. Vérifiez "
        "chronyd sur les deux VMs.",
    )

    ecart = (f2.mtime - f1.mtime).total_seconds()
    assert ecart >= 3.0, message(
        en=f"The two waves are only {ecart:.0f} s apart (web1 at "
        f"{f1.mtime}, web2 at {f2.mtime}).\n"
        "The frontends were handled together, not in successive waves.\n"
        "The brief imposes one host at a time and a 6 second settling period "
        "between waves.",
        fr=f"Les deux vagues sont séparées de {ecart:.0f} s seulement (web1 à "
        f"{f1.mtime}, web2 à {f2.mtime}).\n"
        "Les frontends ont été traités ensemble, pas en vagues successives.\n"
        "L'énoncé impose un hôte à la fois et une stabilisation de 6 secondes "
        "entre les vagues.",
    )


# ─── Tâche 15 — delegate_to / run_once ──────────────────────────────────
def test_15_le_journal_est_ecrit_sur_lhote_delegue(db1):
    """L'état doit apparaître sur db1, et une seule fois.

    Une ligne, pas deux : c'est la preuve de `run_once`. La ligne doit nommer un
    FRONTEND, pas db1 : `delegate_to` déplace l'exécution sans changer
    `inventory_hostname`. Elle doit aussi porter `pool_size`, variable du groupe
    frontends.
    """
    journal = db1.file("/tmp/lab200-central-log.txt")
    assert journal.exists, message(
        en="/tmp/lab200-central-log.txt missing from db1.lab: the task was not "
        "delegated, or not to the right host.",
        fr="/tmp/lab200-central-log.txt absent de db1.lab : la tâche n'a pas été "
        "déléguée, ou pas au bon hôte.",
    )
    assert journal.mode == 0o644, message(
        en=f"The log must be 0644 (task 15), seen: {oct(journal.mode)}.",
        fr=f"Le journal doit être en 0644 (tâche 15), vu : {oct(journal.mode)}.",
    )
    assert journal.user == "root", message(
        en=f"The log must belong to root (task 15), seen: {journal.user}.",
        fr=f"Le journal doit appartenir à root (tâche 15), vu : {journal.user}.",
    )
    lignes = [ln.strip() for ln in journal.content_string.splitlines() if ln.strip()]
    assert len(lignes) == 1, message(
        en=f"The log must contain exactly one line, it has {len(lignes)}:"
        f"\n{lignes}\n"
        "Two lines means the task ran once per frontend. The keyword that "
        "limits a task to a single run per wave is missing.",
        fr=f"Le journal doit contenir exactement une ligne, il en a {len(lignes)} :"
        f"\n{lignes}\n"
        "Deux lignes = la tâche a tourné une fois par frontend. Le mot-clé qui "
        "limite une tâche à une seule exécution par vague manque.",
    )
    assert re.search(r"\bweb[12]\.lab\b", lignes[0]), message(
        en=f"The log line must name the frontend the deployment came from, "
        f"seen: {lignes[0]!r}\n"
        "Delegating does not change the play's host: `inventory_hostname` is "
        "still the frontend's.",
        fr=f"La ligne du journal doit nommer le frontend à l'origine du "
        f"déploiement, vu : {lignes[0]!r}\n"
        "Déléguer ne change pas l'hôte du play : `inventory_hostname` reste "
        "celui du frontend.",
    )
    assert re.search(r"\b8\b", lignes[0]), message(
        en=f"The log line must carry the value of pool_size (8), seen: "
        f"{lignes[0]!r}",
        fr=f"La ligne du journal doit porter la valeur de pool_size (8), vu : "
        f"{lignes[0]!r}",
    )


def test_15b_le_journal_napparait_sur_aucun_frontend(web1, web2):
    """Preuve par l'absence : déléguer, c'est agir AILLEURS."""
    for hote, nom in ((web1, "web1"), (web2, "web2")):
        assert not hote.file("/tmp/lab200-central-log.txt").exists, message(
            en=f"/tmp/lab200-central-log.txt must NOT exist on {nom}.lab: the log is "
            "centralised on db1, so the task must run there.",
            fr=f"/tmp/lab200-central-log.txt ne doit PAS exister sur {nom}.lab : le "
            "journal est centralisé sur db1, la tâche doit s'exécuter là-bas.",
        )


# ─── Tâche 16 — Tâche planifiée ─────────────────────────────────────────
def test_16_la_tache_planifiee_est_dans_la_crontab_de_svcuser(db1):
    """Interroge le planificateur, pas un fichier posé à côté.

    `crontab -l -u svcuser` rend ce que cron exécutera vraiment. On refuse aussi
    le doublon : deux lignes pour le même job = un playbook non idempotent.
    """
    listing = db1.run("crontab -l -u svcuser")
    assert listing.rc == 0, message(
        en="No crontab for svcuser on db1 (`crontab -l -u svcuser` failed):"
        f"\n{listing.stderr.strip()}",
        fr="Aucune crontab pour svcuser sur db1 (`crontab -l -u svcuser` a "
        f"échoué) :\n{listing.stderr.strip()}",
    )
    lignes = [
        ln.strip() for ln in listing.stdout.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    jobs = [ln for ln in lignes if "lab200-audit.log" in ln]
    assert len(jobs) == 1, message(
        en=f"Exactly one entry expected for the report, {len(jobs)} seen.\n"
        f"svcuser's crontab:\n{listing.stdout.strip()}\n"
        "Several identical entries mean the playbook adds one on every run: "
        "the identifier that makes the task idempotent is missing.",
        fr=f"Exactement une entrée attendue pour le rapport, {len(jobs)} vue(s).\n"
        f"Crontab de svcuser :\n{listing.stdout.strip()}\n"
        "Plusieurs entrées identiques signifient que le playbook en rajoute une à "
        "chaque passage : il manque l'identifiant qui rend la tâche idempotente.",
    )
    champs = jobs[0].split()
    assert champs[:5] == ["30", "22", "*", "*", "*"], message(
        en=f"Expected schedule « 30 22 * * * » (22:30 every day), seen: "
        f"« {' '.join(champs[:5])} ».\nFull line: {jobs[0]!r}",
        fr=f"Horaire attendu « 30 22 * * * » (22h30 tous les jours), vu : "
        f"« {' '.join(champs[:5])} ».\nLigne complète : {jobs[0]!r}",
    )
    assert "/usr/bin/date" in jobs[0], message(
        en=f"The scheduled command must be the one from the brief, seen: {jobs[0]!r}",
        fr=f"La commande planifiée doit être celle de l'énoncé, vue : {jobs[0]!r}",
    )


# ─── Tâche 17 — Tags ────────────────────────────────────────────────────
_MARQUEURS_TAGS = {
    "init": "/tmp/lab200-tag-init.txt",
    "publish": "/tmp/lab200-tag-publish.txt",
    "always": "/tmp/lab200-tag-always.txt",
    "purge": "/tmp/lab200-tag-purge.txt",
}


def test_17_les_tags_selectionnent_vraiment_les_taches(db1):
    """Prouve les tags par un VRAI run sélectif, et par ce qu'il pose ou non.

    Le conftest rejoue la solution sans `--tags` : ce run prouve déjà `never` (la
    purge ne doit pas avoir eu lieu). Pour le reste, le test lance lui-même le
    playbook avec `--tags publish`.
    """
    assert not db1.file(_MARQUEURS_TAGS["purge"]).exists, message(
        en="The purge ran although nobody asked for it. A destructive task must be "
        "out of reach of an ordinary run: it is missing the tag that excludes "
        "it by default.",
        fr="La purge a tourné alors que personne ne l'a demandée. Une tâche "
        "destructive doit être hors de portée d'un run ordinaire : il lui manque "
        "le tag qui l'exclut par défaut.",
    )

    db1.check_output("sh -c 'rm -f /tmp/lab200-tag-*.txt'")
    for chemin in _MARQUEURS_TAGS.values():
        assert not db1.file(chemin).exists, message(
            en=f"Clean slate incomplete: {chemin}",
            fr=f"Table rase incomplète : {chemin}",
        )

    res = _lancer_solution("--tags", "publish")
    assert res.returncode == 0, message(
        en="The playbook must run cleanly under « --tags publish ».\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}",
        fr="Le playbook doit se jouer proprement sous « --tags publish ».\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}",
    )

    try:
        assert db1.file(_MARQUEURS_TAGS["publish"]).exists, message(
            en="« --tags publish » did not run the task tagged `publish`.",
            fr="« --tags publish » n'a pas exécuté la tâche taguée `publish`.",
        )
        assert db1.file(_MARQUEURS_TAGS["always"]).exists, message(
            en="The always-run task did not run under « --tags publish ». The tag "
            "that forces a task to run whatever the filter is a reserved tag, "
            "it cannot be invented.",
            fr="La tâche systématique ne s'est pas exécutée sous « --tags publish ». "
            "Le tag qui force une tâche à tourner quel que soit le filtre est un "
            "tag réservé, il ne s'invente pas.",
        )
        assert not db1.file(_MARQUEURS_TAGS["init"]).exists, message(
            en="The task tagged `init` ran under « --tags publish »: tag filtering "
            "does not work. Check that each marker carries its own tag, and "
            "only one.",
            fr="La tâche taguée `init` a tourné sous « --tags publish » : le "
            "filtrage par tags ne fonctionne pas. Vérifiez que chaque marqueur "
            "porte son propre tag, et un seul.",
        )
        assert not db1.file(_MARQUEURS_TAGS["purge"]).exists, message(
            en="The purge ran under « --tags publish » although it must require an "
            "explicit request.",
            fr="La purge a tourné sous « --tags publish » alors qu'elle doit exiger "
            "une demande explicite.",
        )
    finally:
        # Le run sélectif laisse le marqueur d'init manquant : sans cette
        # restauration, le test d'idempotence verrait un `changed` légitime.
        _lancer_solution()

    assert db1.file(_MARQUEURS_TAGS["init"]).exists, message(
        en="The full restore run did not put the init marker back.",
        fr="Le run complet de restauration n'a pas reposé le marqueur d'init.",
    )


# ─── Tâche 18 — Facts personnalisés ─────────────────────────────────────
def test_18_le_fact_personnalise_remonte_vraiment(web1, web2):
    """Le fact doit REMONTER dans une collecte, pas simplement exister.

    On interroge `ansible -m setup` et on lit `ansible_local`. Les valeurs
    viennent des group_vars de la tâche 2.
    """
    for hote in ("web1.lab", "web2.lab"):
        locaux = _facts_locaux(hote)
        assert "lab200" in locaux, message(
            en=f"No `lab200` fact on {hote} (local facts seen: "
            f"{sorted(locaux) or 'none'}).\n"
            "A fact that does not come back is not a fact.\n"
            "Leads: the file name (.fact), its location, its format, and above "
            "all its mode (a data fact must not be executable).",
            fr=f"Aucun fact `lab200` sur {hote} (facts locaux vus : "
            f"{sorted(locaux) or 'aucun'}).\n"
            "Un fact qui ne remonte pas n'est pas un fact.\n"
            "Pistes : le nom du fichier (.fact), son emplacement, son format, et "
            "surtout son mode (un fact de données ne doit pas être exécutable).",
        )
        audit = locaux["lab200"].get("audit")
        assert audit is not None, message(
            en=f"The `lab200` fact of {hote} has no `audit` section, seen: "
            f"{locaux['lab200']}",
            fr=f"Le fact `lab200` de {hote} n'a pas de section `audit`, vu : "
            f"{locaux['lab200']}",
        )
        assert audit.get("stage") == "staging", message(
            en=f"`lab200.audit.stage` must hold the value of deploy_stage "
            f"(« staging ») on {hote}, seen: {audit.get('stage')!r}",
            fr=f"`lab200.audit.stage` doit valoir la valeur de deploy_stage "
            f"(« staging ») sur {hote}, vu : {audit.get('stage')!r}",
        )
        assert str(audit.get("pool")) == "8", message(
            en=f"`lab200.audit.pool` must hold the value of pool_size (8) on "
            f"{hote}, seen: {audit.get('pool')!r}",
            fr=f"`lab200.audit.pool` doit valoir la valeur de pool_size (8) sur "
            f"{hote}, vu : {audit.get('pool')!r}",
        )


def test_11d_le_handler_redemarre_vraiment_httpd(web1):
    """Prouve le handler par le COMPORTEMENT, pas en lisant le YAML du rôle.

    On rend le fichier déployé différent de son template : la tâche template
    rapporte alors `changed`, ce qui doit notifier le handler, qui doit
    redémarrer httpd. Si le handler manque, le PID de httpd ne bouge pas.
    """
    avant = web1.check_output("systemctl show -p MainPID --value httpd")
    assert avant.strip() not in ("", "0"), message(
        en="httpd is not running on web1: the handler cannot be proven.",
        fr="httpd ne tourne pas sur web1 : impossible de prouver le handler.",
    )

    web1.check_output(
        "sh -c 'echo divergence >> /var/www/html/index.html'"
    )
    replay_solution(__file__)

    apres = web1.check_output("systemctl show -p MainPID --value httpd")
    assert apres.strip() not in ("", "0"), message(
        en="httpd no longer runs after the replay: did the handler stop it without "
        "starting it again?",
        fr="httpd ne tourne plus après le rejeu : le handler l'a arrêté sans le "
        "relancer ?",
    )
    assert avant.strip() != apres.strip(), message(
        en="The deployed file was modified, so the template task reported "
        f"`changed`, yet httpd did NOT restart (PID unchanged: {avant.strip()}).\n"
        "Either the template task notifies no handler, or the handler does not "
        "restart httpd.",
        fr="Le fichier déployé a été modifié, la tâche template a donc rapporté "
        f"`changed`, mais httpd n'a PAS redémarré (PID inchangé : {avant.strip()}).\n"
        "Soit la tâche template ne notifie aucun handler, soit le handler ne "
        "redémarre pas httpd.",
    )


# ─── Tâche 19 — Content Collection via requirements.yml ─────────────────────
def test_19_la_collection_est_installee_et_resolvable(db1):
    """La collection épinglée doit être RÉELLEMENT installée et résolvable.

    On ne se fie pas au requirements.yml (une intention), mais à la sortie de
    `ansible-galaxy collection list` déposée sur db1. On exige la version
    ÉPINGLÉE (1.6.2), pas seulement la présence d'ansible.posix : le système
    embarque une autre version de la collection.
    """
    preuve = db1.file("/tmp/lab200-collections.txt")
    assert preuve.exists, message(
        en="/tmp/lab200-collections.txt missing: the collection was not installed "
        "from a requirements.yml, or the inventory was not written on db1.",
        fr="/tmp/lab200-collections.txt absent : la collection n'a pas été installée "
        "depuis un requirements.yml, ou l'inventaire n'a pas été déposé sur db1.",
    )
    assert preuve.mode == 0o644, message(
        en=f"Expected mode 0644, seen: {oct(preuve.mode)}",
        fr=f"Mode attendu 0644, vu : {oct(preuve.mode)}",
    )
    assert preuve.user == "root", message(
        en=f"Expected owner root, seen: {preuve.user}",
        fr=f"Propriétaire attendu root, vu : {preuve.user}",
    )
    contenu = preuve.content_string
    assert "ansible.posix" in contenu, message(
        en="The installation proof does not mention ansible.posix: "
        f"`ansible-galaxy collection list` did not resolve it.\n{contenu[:400]}",
        fr="La preuve d'installation ne mentionne pas ansible.posix : "
        f"`ansible-galaxy collection list` ne l'a pas résolue.\n{contenu[:400]}",
    )
    assert "1.6.2" in contenu, message(
        en="The pinned version 1.6.2 does not appear in the collection inventory: "
        "the requirements.yml did not install the requested version "
        f"(strict semver pinning required).\n{contenu[:400]}",
        fr="La version épinglée 1.6.2 n'apparaît pas dans l'inventaire des "
        "collections : le requirements.yml n'a pas installé la version demandée "
        f"(pinning semver strict exigé).\n{contenu[:400]}",
    )


def test_19b_un_module_de_la_collection_a_ete_utilise(db1):
    """Prouve l'USAGE de la collection par l'état qu'un de ses modules a posé.

    Installer une collection ne suffit pas : l'objectif EX294 est de « s'en
    servir dans un playbook ». ansible.posix.sysctl est un module fourni par la
    collection installée ; son effet se lit dans le paramètre noyau appliqué ET
    dans le fichier persistant qu'il écrit. Un fichier obtenu par un simple
    `copy` de builtin ne prouverait rien : on vérifie donc que vm.swappiness vaut
    réellement 25 sur la machine.
    """
    conf = db1.file("/etc/sysctl.d/99-lab200-collection.conf")
    assert conf.exists, message(
        en="/etc/sysctl.d/99-lab200-collection.conf missing: no module from the "
        "installed collection wrote the sysctl parameter (task 19).",
        fr="/etc/sysctl.d/99-lab200-collection.conf absent : aucun module de la "
        "collection installée n'a écrit le paramètre sysctl (tâche 19).",
    )
    contenu = conf.content_string
    assert re.search(r"vm\.swappiness\s*=\s*25", contenu), message(
        en="The sysctl file must carry « vm.swappiness = 25 » (task 19).\n"
        f"Contents: {contenu.strip()[:200]}",
        fr="Le fichier sysctl doit porter « vm.swappiness = 25 » (tâche 19).\n"
        f"Contenu : {contenu.strip()[:200]}",
    )
    live = db1.run("sysctl -n vm.swappiness")
    assert live.rc == 0 and live.stdout.strip() == "25", message(
        en="vm.swappiness must be 25 on the machine (ansible.posix.sysctl module "
        f"applied), seen: {live.stdout.strip()!r}.\n"
        "A sysctl file written without being applied does not prove the "
        "collection module was used.",
        fr="vm.swappiness doit valoir 25 sur la machine (module ansible.posix.sysctl "
        f"appliqué), vu : {live.stdout.strip()!r}.\n"
        "Un fichier sysctl écrit sans être appliqué ne prouve pas l'usage du "
        "module de collection.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE)."""
    assert_idempotent(__file__)


# ----------------------------------------------------------------------
# La preuve de persistance. Volontairement en DERNIER : il redémarre les VMs.
# ----------------------------------------------------------------------


@pytest.mark.slow
def test_99_persistance_reelle_apres_reboot():
    """Redémarre web1 et db1, puis re-vérifie l'état RUNTIME.

    La persistance est LE piège qui fait échouer les candidats RHCE. Un capstone
    qui la certifie sans jamais redémarrer certifie une hypothèse.
    """
    web1 = reboot_and_wait("web1.lab")
    db1 = reboot_and_wait("db1.lab")

    # Tâche 8 : le booléen doit être ON au runtime, après redémarrage.
    out = web1.check_output("getsebool httpd_can_network_connect_db")
    valeur = out.split("-->")[-1].strip()
    assert valeur == "on", message(
        en="After reboot, httpd_can_network_connect_db fell back to "
        f"« {valeur} »: setsebool was used without -P.",
        fr="Après reboot, httpd_can_network_connect_db est retombé à "
        f"« {valeur} » : setsebool a été utilisé sans -P.",
    )

    # Tâche 9 : les règles doivent être ouvertes au runtime, après redémarrage.
    services_web1 = web1.check_output("firewall-cmd --list-services")
    for svc in ("http", "https"):
        assert svc in services_web1.split(), message(
            en=f"After reboot, {svc} is no longer open on web1 (active services: "
            f"{services_web1.strip()}).",
            fr=f"Après reboot, {svc} n'est plus ouvert sur web1 (services actifs : "
            f"{services_web1.strip()}).",
        )
    ports_db1 = db1.check_output("firewall-cmd --list-ports")
    assert "6379/tcp" in ports_db1.split(), message(
        en=f"After reboot, 6379/tcp is no longer open on db1 (active ports: "
        f"{ports_db1.strip()}).",
        fr=f"Après reboot, 6379/tcp n'est plus ouvert sur db1 (ports actifs : "
        f"{ports_db1.strip()}).",
    )

    # Tâche 10 : le montage LVM doit être remonté par le système, seul.
    monte = db1.run("findmnt --noheadings --target /srv/appdata")
    assert monte.rc == 0, message(
        en="After reboot, /srv/appdata is no longer mounted: the fstab entry is "
        "missing, wrong, or the logical volume is not activated at boot.",
        fr="Après reboot, /srv/appdata n'est plus monté : l'entrée fstab est "
        "absente, fausse, ou le volume logique n'est pas activé au démarrage.",
    )

    # Le service doit revenir seul : `enabled` sans reboot ne le prouve pas.
    assert web1.service("httpd").is_running, message(
        en="After reboot, httpd no longer runs on web1: the service was started "
        "without being enabled (`enabled: true`).",
        fr="Après reboot, httpd ne tourne plus sur web1 : le service a été démarré "
        "sans être activé (`enabled: true`).",
    )

    # Tâche 16 : la tâche planifiée doit survivre, et crond doit tourner.
    listing = db1.run("crontab -l -u svcuser")
    assert listing.rc == 0 and "lab200-audit.log" in listing.stdout, message(
        en="After reboot, svcuser's scheduled task is gone.\n"
        f"Crontab seen:\n{listing.stdout.strip() or '(empty)'}",
        fr="Après reboot, la tâche planifiée de svcuser a disparu.\n"
        f"Crontab vue :\n{listing.stdout.strip() or '(vide)'}",
    )
    assert db1.service("crond").is_running, message(
        en="After reboot, crond no longer runs on db1: the scheduled task is "
        "properly written, and will never fire.",
        fr="Après reboot, crond ne tourne plus sur db1 : la tâche planifiée est "
        "bien écrite, et ne partira jamais.",
    )

    # Tâche 18 : le fact doit remonter sur une machine qui vient de démarrer.
    locaux = _facts_locaux("web1.lab")
    assert "lab200" in locaux, message(
        en="After reboot, the `lab200` fact no longer comes back on web1 (local "
        f"facts seen: {sorted(locaux) or 'none'}).",
        fr="Après reboot, le fact `lab200` ne remonte plus sur web1 (facts locaux "
        f"vus : {sorted(locaux) or 'aucun'}).",
    )

    # Tâche 19 : le paramètre sysctl posé par le module de collection doit
    # survivre au reboot (le fichier /etc/sysctl.d/ est réappliqué au boot).
    live = db1.run("sysctl -n vm.swappiness")
    assert live.rc == 0 and live.stdout.strip() == "25", message(
        en="After reboot, vm.swappiness is no longer 25: the parameter was set at "
        "runtime without a persistent file in /etc/sysctl.d/.\n"
        f"Seen: {live.stdout.strip()!r}",
        fr="Après reboot, vm.swappiness n'est plus à 25 : le paramètre a été posé "
        "en runtime sans fichier persistant dans /etc/sysctl.d/.\n"
        f"Vu : {live.stdout.strip()!r}",
    )
