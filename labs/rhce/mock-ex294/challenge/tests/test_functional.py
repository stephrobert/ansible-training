"""Tests pytest+testinfra pour le mock RHCE EX294 (lab 100).

Un test au moins par tâche du mock, et plusieurs pour les tâches qui se ratent
en morceaux plutôt qu'en bloc.
"""

import json
import os
import re
import subprocess

import pytest
import yaml

from conftest import (
    REPO_ROOT, lab_host, lab_playbook, lab_solution_text, lab_inventory_args,
    assert_idempotent, reboot_and_wait, replay_solution, _EXTRA_ARGS, _roles_path,
)

_LAB_ROOT = REPO_ROOT / "labs" / "rhce" / "mock-ex294"
_LAB_KEY = "rhce/mock-ex294"

# L'inventaire de la tâche 1. C'est le chemin que le conftest passe en -i à
# ansible-playbook (table _EXTRA_ARGS), donc le seul qui compte ici.

# Emplacements possibles du rôle app_deploy de la tâche 11, dans l'ordre de
# priorité. Le challenge/README impose `roles/` à la racine du lab ; le
# conftest accepte aussi `challenge/roles/` via ANSIBLE_ROLES_PATH.
_ROLE_DIRS = (
    "roles/app_deploy",
    "challenge/roles/app_deploy",
)


def _role_file(relpath):
    """Retourne le YAML parsé d'un fichier du rôle app_deploy, ou None.

    Même arbitrage que `lab_playbook` dans le conftest : le travail de
    l'apprenant s'il existe, sinon la solution de référence du formateur. Le
    test codait en dur `labs/rhce/mock-ex294/roles/app_deploy`, un chemin qui
    n'existe QUE chez l'apprenant : en mode formateur il échouait sur un rôle
    « absent » alors que la référence en livre un.

    Le repli sur la référence est conditionné à l'ABSENCE de
    `challenge/solution.yml`, c'est-à-dire au mode formateur, exactement comme
    le conftest discrimine les deux modes. Sans cette garde, un apprenant qui
    n'écrit aucun rôle verrait le test valider celui du formateur : le mock
    certifierait le travail de quelqu'un d'autre.

    La référence étant chiffrée par ansible-vault, on passe par
    `lab_solution_text`, qui la déchiffre à la volée : la lire directement
    rendrait le corps chiffré, dans lequel aucun handler n'apparaît.

    Args:
        relpath: chemin du fichier dans le rôle (ex : "handlers/main.yml").

    Returns:
        L'objet YAML chargé, ou None si le fichier n'existe nulle part.
    """
    lab_root = REPO_ROOT / "labs" / "rhce" / "mock-ex294"
    for role_dir in _ROLE_DIRS:
        path = lab_root / role_dir / relpath
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if (lab_root / "challenge" / "solution.yml").exists():
        return None  # mode apprenant : on n'inspecte que SON rôle
    reference = REPO_ROOT / "solution" / "rhce" / "mock-ex294" / "roles" / "app_deploy"
    if not (reference / relpath).is_file():
        return None
    return yaml.safe_load(
        lab_solution_text(__file__, name=f"roles/app_deploy/{relpath}")
    ) or []


def _lancer_solution(*args_supplementaires):
    """Lance le playbook du lab, en autorisant des arguments en plus.

    `replay_solution` du conftest ne sait pas passer `--tags`, et ne rend que
    ok/changed/failed du PLAY RECAP : ni `rescued`, ni `ignored`. Or ce sont
    justement les deux compteurs qui prouvent la tâche 13, et `--tags` est le
    seul moyen de prouver la tâche 17 sans lire le YAML.

    On reconstruit donc ici la même commande que le conftest, sans le modifier :
    même arbitrage apprenant/formateur (`lab_playbook`), même inventaire
    (`lab_inventory_args`), mêmes options vault (`_EXTRA_ARGS`) et même
    ANSIBLE_ROLES_PATH (`_roles_path`, nécessaire même sous `--tags` : Ansible
    résout les rôles à la compilation du play, avant tout filtrage par tag).

    Returns:
        Le CompletedProcess, rendu tel quel : l'appelant décide si un rc non nul
        est un échec ou l'objet même du test.
    """
    playbook, args_vault = lab_playbook(__file__)
    cmd = ["ansible-playbook", *args_vault, str(playbook.relative_to(REPO_ROOT))]
    cmd += _EXTRA_ARGS[_LAB_KEY]
    cmd += lab_inventory_args(__file__)
    cmd += list(args_supplementaires)
    env = os.environ.copy()
    env.update(_roles_path(_LAB_ROOT))
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env)


def _recap_de(sortie, hote):
    """Extrait les compteurs du PLAY RECAP pour un hôte donné.

    Returns:
        dict {"ok": int, "changed": int, "failed": int, "rescued": int, ...}
        pour tous les compteurs présents sur la ligne.
    """
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

    On n'inspecte pas le fichier .fact : on demande à Ansible ce qu'il voit.
    Un .fact présent mais mal formé, mal nommé, ou posé en 0755 (donc exécuté
    au lieu d'être lu) ne remonte pas, et c'est tout ce qui compte : un fact que
    personne ne peut lire n'est pas un fact.

    La collecte se fait sans `become`, comme le ferait n'importe quel play :
    c'est aussi ce qui vérifie que les droits demandés par l'énoncé (0755 sur le
    répertoire, 0644 sur le fichier) sont bien ceux posés.

    Returns:
        Le dict `ansible_local` de l'hôte (vide s'il n'a aucun fact local).
    """
    res = subprocess.run(
        ["ansible", *lab_inventory_args(__file__), hote,
         "-m", "ansible.builtin.setup", "-a", "filter=ansible_local"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"La collecte de facts a échoué sur {hote} :\n"
        f"--- stdout ---\n{res.stdout.strip()}\n"
        f"--- stderr ---\n{res.stderr.strip()}"
    )
    # Format ad hoc : « web1.lab | SUCCESS => { ... } ».
    _, _, corps = res.stdout.partition("=>")
    assert corps.strip(), f"Sortie inattendue de la collecte sur {hote} :\n{res.stdout}"
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
    """L'inventaire doit déclarer les deux groupes ET joindre leurs hôtes.

    Le test se contentait de vérifier que db1 et web1 tournaient sous
    AlmaLinux. Il passait par le ssh_config de testinfra, donc SANS jamais
    ouvrir l'inventaire du candidat : il était vert même avec zéro fichier
    écrit, et rouge seulement si l'infra était éteinte. La tâche 1 n'était pas
    testée.

    On interroge ici l'inventaire EFFECTIF tel qu'Ansible le résout
    (`ansible-inventory --graph`), pas le texte du fichier, puis on prouve
    qu'il fonctionne vraiment en joignant les 3 hôtes à travers lui : un
    inventaire syntaxiquement correct mais qui déclare le mauvais utilisateur
    ne vaut rien un jour d'examen.
    """
    graph = subprocess.run(
        ["ansible-inventory", *lab_inventory_args(__file__), "--graph"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert graph.returncode == 0, (
        "ansible-inventory n'a pas su lire l'inventaire du lab :\n"
        f"{graph.stderr.strip()}"
    )
    out = graph.stdout
    for group, members in (
        ("webservers", ("web1.lab", "web2.lab")),
        ("dbservers", ("db1.lab",)),
    ):
        assert f"@{group}:" in out, (
            f"Groupe {group} absent de l'inventaire.\nVu :\n{out.strip()}"
        )
        section = out.split(f"@{group}:", 1)[1].split("@", 1)[0]
        for member in members:
            assert member in section, (
                f"{member} doit appartenir au groupe {group}.\n"
                f"Vu :\n{out.strip()}"
            )

    ping = subprocess.run(
        ["ansible", *lab_inventory_args(__file__), "all",
         "-m", "ansible.builtin.ping"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert ping.returncode == 0, (
        "Les 3 hôtes doivent répondre au ping Ansible à travers VOTRE "
        f"inventaire.\n--- stdout ---\n{ping.stdout.strip()}\n"
        f"--- stderr ---\n{ping.stderr.strip()}"
    )
    assert ping.stdout.count('"ping": "pong"') == 3, (
        "3 'pong' attendus (web1, web2, db1).\n"
        f"--- stdout ---\n{ping.stdout.strip()}"
    )


# ─── Tâche 2 — Variables (vérifié sur un fichier produit par le playbook) ──
# Le playbook doit poser /tmp/lab100-vars.txt sur web1 contenant les vars résolues.
def test_02_variables_precedence(web1):
    """Tâche 2 : group_vars + host_vars correctement résolus."""
    f = web1.file("/tmp/lab100-vars.txt")
    assert f.exists, "Le playbook doit déposer /tmp/lab100-vars.txt sur web1"
    content = f.content_string
    assert "production" in content, "app_env doit valoir 'production'"
    assert "worker_count: 4" in content or "worker_count = 4" in content


# ─── Tâche 3 — Vault ─────────────────────────────────────────────────────
def test_03_vault_decrypted(db1):
    f = db1.file("/tmp/lab100-vault-test.txt")
    assert f.exists, "/tmp/lab100-vault-test.txt absent — vars_files vault.yml KO"
    assert f.mode == 0o600, f"Mode attendu 0600, vu : {oct(f.mode)}"
    assert "Lab92Pass" in f.content_string, "db_password déchiffré attendu"


# ─── Tâche 4 — Templates et fichiers ────────────────────────────────────
def test_04_template_app_conf(db1):
    f = db1.file("/tmp/lab100-app.conf")
    assert f.exists
    assert f.mode == 0o640, f"Mode attendu 0640, vu : {oct(f.mode)}"
    assert f.user == "appuser"
    assert f.group == "appgroup"
    content = f.content_string
    assert "lab100db" in content, "db_name doit apparaître"
    # TROU T4 : l'énoncé exige que le rendu contienne « au minimum le nom d'hôte
    # Ansible ET db_name ». Seul db_name était vérifié : un template qui aurait
    # oublié `ansible_hostname` passait, alors que c'est précisément ce qui
    # prouve qu'il est rendu PAR HÔTE et non figé. La solution émet
    # `hostname={{ ansible_hostname }}`, soit « db1 » sur db1.lab.
    assert re.search(r"\bdb1\b", content), (
        "Le rendu de /tmp/lab100-app.conf doit contenir le nom d'hôte Ansible "
        f"(« db1 » sur db1.lab), absent du contenu :\n{content.strip()[:200]}\n"
        "Sans lui, ce n'est pas un template rendu par hôte."
    )


# ─── Tâche 5 — Paquets ──────────────────────────────────────────────────
def test_05_packages_installed(db1, web1, web2):
    assert db1.package("nginx").is_installed
    assert db1.package("mariadb-server").is_installed
    assert db1.package("python3-libselinux").is_installed
    # TROU T5 : python3-libselinux est exigé « sur TOUS les hôtes » et n'était
    # vérifié que sur db1. Sur les webservers, c'est ce paquet qui fournit les
    # liaisons Python dont ansible.posix.seboolean a besoin (tâche 8) : absent,
    # la gestion du booléen SELinux échoue. La solution l'installe sur `all`.
    for host, nom in ((web1, "web1"), (web2, "web2")):
        assert host.package("python3-libselinux").is_installed, (
            f"python3-libselinux doit être installé sur {nom}.lab : l'énoncé "
            "l'exige sur tous les hôtes, seul db1 était contrôlé."
        )


# ─── Tâche 6 — Services ─────────────────────────────────────────────────
def test_06_services_running(web1, db1):
    assert web1.service("nginx").is_running, "nginx KO sur web1"
    assert web1.service("nginx").is_enabled
    assert db1.service("mariadb").is_running, "mariadb KO sur db1"
    # `enabled` était vérifié pour nginx et OUBLIÉ pour mariadb : la tâche 6
    # exige les deux services « démarrés ET activés au boot », et la moitié de
    # cette exigence n'était prouvée nulle part.
    assert db1.service("mariadb").is_enabled, (
        "mariadb tourne sur db1 mais n'est pas activé au boot : il ne "
        "reviendrait pas après un redémarrage (tâche 6)."
    )


# ─── Tâche 7 — Utilisateurs ─────────────────────────────────────────────
def test_07_user_appuser(db1):
    user = db1.user("appuser")
    assert user.exists
    assert user.uid == 2001
    assert user.group == "appgroup"
    # TROU T7 : le shell /bin/bash est exigé par l'énoncé et n'était pas testé.
    # Un `user:` sans `shell:` hérite du défaut de useradd (souvent /bin/bash,
    # mais pas garanti, et /sbin/nologin sur certains gabarits) : l'exiger
    # explicitement, comme le fait la solution (`shell: /bin/bash`).
    assert user.shell == "/bin/bash", (
        f"appuser doit avoir le shell /bin/bash (tâche 7), vu : {user.shell!r}."
    )
    grp = db1.group("appgroup")
    assert grp.exists
    assert grp.gid == 2001


def test_07b_appuser_sudo_systemctl_nopasswd(db1):
    """appuser doit lancer systemctl en sudo SANS mot de passe, et RIEN d'autre.

    L'énoncé l'exige explicitement (« uniquement cette commande ») et rien ne le
    vérifiait : un candidat pouvait accorder un ALL=(ALL) NOPASSWD:ALL et passer.
    On interroge la politique sudo effective plutôt que le fichier : c'est
    l'état réel qui compte, peu importe où la règle est écrite.
    """
    allowed = db1.run("sudo -l -U appuser 2>/dev/null")
    assert allowed.rc == 0, (
        "Impossible de lire la politique sudo d'appuser (sudo -l -U appuser)."
    )
    out = allowed.stdout
    assert "NOPASSWD" in out and "/usr/bin/systemctl" in out, (
        "appuser doit pouvoir exécuter /usr/bin/systemctl en sudo sans mot de "
        f"passe.\nPolitique vue :\n{out.strip()}\n"
        "Déclarez la règle dans /etc/sudoers.d/ (validée par visudo -cf)."
    )
    # « uniquement cette commande » : un blanc-seing est une faute de sécurité,
    # sanctionnée à l'examen.
    assert not re.search(r"NOPASSWD:\s*ALL\b", out), (
        "appuser a un sudo NOPASSWD sur TOUTES les commandes.\n"
        f"Politique vue :\n{out.strip()}\n"
        "L'énoncé demande uniquement /usr/bin/systemctl : restreignez la règle."
    )


# ─── Tâche 8 — SELinux ──────────────────────────────────────────────────
def test_08_selinux_httpd_can_network_connect(web1):
    """Le booléen doit être actif dans le noyau, ici et maintenant.

    Le test cherchait `"on" in stdout`. Or getsebool répond
    « httpd_can_network_connect --> off » : la sous-chaîne « on » est déjà dans
    « c-on-nect ». Le test était donc VERT quel que soit l'état du booléen, y
    compris à off. On lit la valeur après la flèche, seule chose qui compte.
    """
    cmd = web1.run("getsebool httpd_can_network_connect")
    assert cmd.rc == 0, f"getsebool a échoué : {cmd.stderr.strip()}"
    value = cmd.stdout.rsplit("-->", 1)[-1].strip()
    assert value == "on", (
        f"httpd_can_network_connect doit être activé, vu : {value or '?'}\n"
        f"Sortie complète : {cmd.stdout.strip()}"
    )


def test_08b_selinux_boolean_persistent(web1):
    """Le booléen doit survivre au reboot (SELinux : valeur « persistent »).

    `setsebool` sans -P ne tient que jusqu'au redémarrage : c'est l'erreur
    classique qui fait perdre les points à l'examen, alors que getsebool est
    vert juste après.
    """
    cmd = web1.run("semanage boolean -l | grep '^httpd_can_network_connect'")
    assert cmd.rc == 0, (
        "Impossible de lire la valeur persistante du booléen "
        "(semanage boolean -l)."
    )
    # Format : « nom  (actuel , persistant)  description »
    assert re.search(r"\(\s*on\s*,\s*on\s*\)", cmd.stdout), (
        "httpd_can_network_connect doit être activé DE FAÇON PERSISTANTE.\n"
        f"Vu : {cmd.stdout.strip()}\n"
        "Le second champ est la valeur au prochain boot : elle doit être « on ». "
        "Le module ansible.posix.seboolean prend un paramètre pour cela."
    )


# ─── Tâche 9 — Firewalld ────────────────────────────────────────────────
def test_09_firewall_http_https_open(web1):
    cmd = web1.run("firewall-cmd --list-services")
    assert "http" in cmd.stdout
    assert "https" in cmd.stdout


def test_09b_firewall_mysql_db1(db1):
    cmd = db1.run("firewall-cmd --list-services")
    assert "mysql" in cmd.stdout


def test_09c_firewall_rules_are_permanent(web1, db1):
    """Les règles doivent être dans la configuration PERMANENTE, pas seulement
    dans le runtime.

    `firewall-cmd --add-service=http` sans --permanent est perdu au reboot.
    `--list-services` seul ne voit que le runtime : il est vert dans les deux
    cas, d'où le piège.
    """
    out = web1.run("firewall-cmd --permanent --list-services")
    for svc in ("http", "https"):
        assert svc in out.stdout, (
            f"Le service {svc} doit être ouvert de façon PERMANENTE sur web1 "
            f"(vu en permanent : {out.stdout.strip()}).\n"
            "Une règle runtime disparaît au redémarrage. Le module "
            "ansible.posix.firewalld a un paramètre pour cela."
        )
    out = db1.run("firewall-cmd --permanent --list-services")
    assert "mysql" in out.stdout, (
        f"Le service mysql doit être ouvert de façon PERMANENTE sur db1 "
        f"(vu en permanent : {out.stdout.strip()})."
    )


# ─── Tâche 10 — Stockage ────────────────────────────────────────────────
def test_10_lvm_xfs_mounted(db1):
    mount = db1.mount_point("/mnt/data")
    assert mount.exists, "/mnt/data doit être monté"
    assert mount.filesystem == "xfs"


def test_10b_mount_persistent_fstab(db1):
    """Le montage doit être déclaré dans /etc/fstab (persistance reboot).

    Un `mount` manuel ou un module mount en state=mounted sans entrée fstab
    disparaît au redémarrage. C'est le grand classique de l'examen : la machine
    est correcte à l'instant T, et fausse après reboot.
    """
    fstab = db1.file("/etc/fstab").content_string
    line = next(
        (
            ln for ln in fstab.splitlines()
            if not ln.lstrip().startswith("#") and " /mnt/data " in f" {ln} "
        ),
        None,
    )
    assert line is not None, (
        "Aucune entrée /mnt/data active dans /etc/fstab : le montage ne "
        "survivra pas au reboot.\n"
        "Le module ansible.posix.mount écrit dans fstab avec state=mounted "
        "(et non state=ephemeral)."
    )
    assert "xfs" in line, (
        f"L'entrée fstab de /mnt/data doit être en xfs (vu : {line.strip()})."
    )


def test_10c_lv_data_nom_et_taille(db1):
    """Le volume logique doit s'appeler lv_data et faire ~300 Mo (tâche 10).

    test_10 prouve qu'un système XFS est monté sur /mnt/data, mais pas que
    c'est le BON volume : un LV nommé autrement, ou dimensionné à 100 Mo au
    lieu de 300, monterait aussi bien et passerait. L'énoncé impose le nom
    exact `lv_data` et la taille 300 Mo ; la solution crée `lvol: lv=lv_data
    size=300M` dans le VG vg_lab. La taille est arrondie au multiple d'extents
    (4 Mo), d'où une tolérance de quelques Mo.
    """
    res = db1.run(
        "lvs --noheadings --nosuffix --units m -o lv_name,lv_size vg_lab"
    )
    assert res.rc == 0, (
        f"Impossible de lister les LV du VG vg_lab sur db1 : {res.stderr.strip()}"
    )
    tailles = {}
    for ligne in res.stdout.strip().splitlines():
        champs = ligne.split()
        if len(champs) >= 2:
            try:
                tailles[champs[0]] = float(champs[1])
            except ValueError:
                continue
    assert "lv_data" in tailles, (
        f"Aucun LV nommé « lv_data » dans vg_lab (vus : {sorted(tailles) or 'aucun'}).\n"
        "L'énoncé impose ce nom exact : un LV correctement monté mais mal nommé "
        "ne vaut rien à l'examen."
    )
    taille = tailles["lv_data"]
    assert abs(taille - 300.0) <= 16.0, (
        f"lv_data doit faire ~300 Mo, mesuré : {taille:.0f} Mo.\n"
        "La taille est un critère de la tâche 10, au même titre que le montage."
    )


# ─── Tâche 11 — Rôle app_deploy ─────────────────────────────────────────
def test_11_role_index_html(web1, web2):
    for host in (web1, web2):
        f = host.file("/usr/share/nginx/html/index.html")
        assert f.exists, f"index.html absent sur {host.system_info.hostname}"


def test_11b_template_contient_le_hostname(web1, web2):
    """Le template doit produire un contenu PAR HÔTE, pas un fichier statique.

    L'énoncé exige « au moins le nom d'hôte d'inventaire ». Sans ce test, un
    simple `copy:` d'un index.html figé passait : le lab n'aurait pas prouvé
    qu'un template est un template.
    """
    for host, name in ((web1, "web1"), (web2, "web2")):
        content = host.file("/usr/share/nginx/html/index.html").content_string
        assert name in content, (
            f"index.html sur {name}.lab ne contient pas son nom d'hôte "
            f"d'inventaire.\nContenu : {content.strip()[:200]}\n"
            "Le template doit être rendu par hôte (inventory_hostname), sinon "
            "ce n'est pas un template mais une copie."
        )


def test_11c_role_declare_un_handler(web1):
    """Le rôle doit déclarer un handler notifié par la tâche de template.

    Ici on lit le rôle, et c'est assumé : un handler qui n'est jamais notifié
    ne laisse aucune trace dans l'état final du système, donc testinfra ne peut
    pas le voir. On contrôle donc la STRUCTURE du rôle (YAML chargé, pas une
    sous-chaîne), ce qui reste la seule preuve accessible.
    """
    handlers = _role_file("handlers/main.yml")
    if handlers is None:
        handlers = _role_file("handlers/main.yaml")
    assert handlers is not None, (
        "Le rôle app_deploy doit déclarer un handler dans "
        "labs/rhce/mock-ex294/roles/app_deploy/handlers/main.yml (absent)."
    )
    names = {h.get("name", "") for h in handlers if isinstance(h, dict)}
    assert any("nginx" in n.lower() for n in names), (
        "Aucun handler concernant nginx dans le rôle app_deploy "
        f"(handlers vus : {sorted(names) or 'aucun'})."
    )

    tasks = _role_file("tasks/main.yml")
    if tasks is None:
        tasks = _role_file("tasks/main.yaml")
    assert tasks is not None, "Le rôle app_deploy doit avoir tasks/main.yml."
    notifying = [
        t for t in tasks
        if isinstance(t, dict) and t.get("notify")
        and any(k.endswith("template") for k in t)
    ]
    assert notifying, (
        "La tâche qui déploie le template doit notifier le handler "
        "(mot-clé `notify:`). Sans notification, le handler ne tourne jamais et "
        "nginx ne relit pas sa configuration."
    )


# ─── Tâche 12 — Conditions et boucles ───────────────────────────────────
def test_12_loop_5_files_parity(db1):
    """Les 5 fichiers doivent porter LEUR parité, pas celle du voisin.

    Le test cherchait `parity in content`. Or « pair » est une sous-chaîne
    d'« impair » : une boucle qui écrivait « impair » dans les cinq fichiers
    passait les assertions des fichiers pairs. On exige donc le mot entier
    (`\\bpair\\b` ne matche pas « impair »), ce qui reste tolérant sur la
    tournure de la phrase mais plus sur la parité elle-même.
    """
    expected = {
        1: "impair",
        2: "pair",
        3: "impair",
        4: "pair",
        5: "impair",
    }
    for n, parity in expected.items():
        f = db1.file(f"/tmp/file{n}")
        assert f.exists, f"/tmp/file{n} absent"
        content = f.content_string
        assert re.search(rf"\b{parity}\b", content), (
            f"/tmp/file{n} doit contenir le mot '{parity}', vu : "
            f"{content.strip()[:50]!r}\n"
            "Attention : la condition de parité doit porter sur le numéro du "
            "fichier, et 'pair' est une sous-chaîne d'‘impair’."
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


def test_12b_les_cinq_fichiers_en_une_seule_tache():
    """L'énoncé impose que les 5 fichiers de parité tiennent en UNE tâche.

    C'est une contrainte de STRUCTURE, invisible dans l'état final : cinq
    `copy:` séparés produiraient exactement les mêmes /tmp/fileN et passeraient
    test_12. On la vérifie donc sur la solution effectivement jouée (celle de
    l'apprenant si elle existe, sinon la référence, via `lab_solution_text`),
    comme les autres contrôles structurels de ce fichier : on compte les tâches
    qui créent un /tmp/fileN et on exige qu'il n'y en ait qu'une, munie d'une
    boucle. La solution le fait en un `copy` + `loop: [1..5]`.
    """
    plays = yaml.safe_load(lab_solution_text(__file__)) or []
    motif = re.compile(r"/tmp/file(\d|\{\{)")
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
    assert len(cibles) == 1, (
        f"La tâche 12 doit créer /tmp/file1..5 en UNE SEULE tâche (avec une "
        f"boucle), or {len(cibles)} tâche(s) créent ces fichiers.\n"
        "Cinq tâches séparées produisent le même état mais violent l'énoncé "
        "« les 5 fichiers doivent être créés dans une seule tâche »."
    )
    unique = cibles[0]
    assert any(cle in unique for cle in ("loop", "with_items", "with_sequence")), (
        "La tâche qui crée les 5 fichiers doit porter une boucle (`loop:`), "
        "sinon elle ne peut pas produire 5 fichiers en une seule tâche.\n"
        f"Clés de la tâche vue : {sorted(unique)}"
    )


# ─── Tâche 13 — block / rescue / always ─────────────────────────────────
@pytest.fixture(scope="module")
def run_complet():
    """Un run complet du playbook, dont on garde la sortie brute.

    Le PLAY RECAP est le seul endroit où l'on peut lire `rescued` et `ignored`.
    Un seul run suffit pour les deux assertions de la tâche 13 : on le partage.
    """
    res = _lancer_solution()
    assert res.returncode == 0, (
        "Le playbook doit se terminer en succès : un rescue qui rattrape une "
        "erreur rend un rc nul.\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}"
    )
    return res.stdout


def test_13_le_rescue_a_vraiment_rattrape_un_echec(run_complet):
    """Prouve le rescue par les compteurs du PLAY RECAP, pas par le YAML.

    `rescued=1` ne s'obtient d'aucune autre façon : il faut qu'une tâche d'un
    `block` ait RÉELLEMENT échoué et qu'un `rescue` l'ait rattrapée. Un block
    dont rien n'échoue affiche `rescued=0`, et un rescue déclaré mais placé sur
    un block qui réussit toujours ne prouve rien du tout.

    `ignored=0` ferme la porte de sortie : `ignore_errors: true` fait aussi
    passer le playbook au vert, mais il TAIT l'erreur au lieu de la traiter, et
    ne déclenche aucun rescue. Le RECAP les distingue formellement
    (`ignored=1 rescued=0`), là où l'état final des deux serait identique si on
    posait les marqueurs à la main.

    `failed=0` prouve le dernier tiers de l'énoncé : le play a continué.
    """
    recap = _recap_de(run_complet, "db1.lab")
    assert recap.get("rescued", 0) >= 1, (
        "Aucun rescue n'a été déclenché sur db1 (rescued="
        f"{recap.get('rescued', 0)}).\n"
        "La tâche du block doit échouer POUR DE VRAI et le rescue doit la "
        "rattraper. Un block dont aucune tâche ne plante ne prouve rien.\n"
        f"RECAP db1 : {recap}"
    )
    assert recap.get("ignored", 0) == 0, (
        f"db1 rapporte ignored={recap.get('ignored')} : une erreur a été mise "
        "sous le tapis avec `ignore_errors` au lieu d'être traitée par un "
        "`rescue`. L'énoncé demande de consigner l'incident, pas de l'ignorer.\n"
        f"RECAP db1 : {recap}"
    )
    assert recap["failed"] == 0, (
        f"Le play doit se poursuivre malgré l'incident (failed={recap['failed']}).\n"
        f"RECAP db1 : {recap}"
    )


def test_13b_le_rescue_et_le_always_ont_laisse_leurs_traces(db1):
    """Les deux marqueurs du bloc, et l'identité de la tâche qui a échoué.

    Le contenu attendu est le nom exact imposé par l'énoncé à la tâche qui
    échoue. Il se lit dans `ansible_failed_task`, une variable qui n'EXISTE que
    dans un `rescue` : le fichier ne peut pas être produit ailleurs sans que le
    play plante sur une variable indéfinie.

    On compare la ligne entière, pas une sous-chaîne : `in` accepterait
    « Démarrer le collecteur lab100-autre-chose ».
    """
    incident = db1.file("/tmp/lab100-incident.txt")
    assert incident.exists, (
        "/tmp/lab100-incident.txt absent : le rescue n'a pas consigné "
        "l'incident."
    )
    assert incident.mode == 0o644, f"Mode attendu 0644, vu : {oct(incident.mode)}"
    lignes = [ln.strip() for ln in incident.content_string.splitlines() if ln.strip()]
    assert "Démarrer le collecteur lab100" in lignes, (
        "/tmp/lab100-incident.txt doit contenir le nom de la tâche qui a "
        "échoué, tel qu'Ansible le rapporte, sur une ligne à lui.\n"
        f"Lignes vues : {lignes}\n"
        "La variable qui le porte n'est disponible que dans un `rescue`."
    )

    fin = db1.file("/tmp/lab100-incident-fin.txt")
    assert fin.exists, (
        "/tmp/lab100-incident-fin.txt absent : la section qui doit s'exécuter "
        "dans TOUS les cas ne l'a pas fait, alors que le bloc a justement "
        "échoué. C'est le cas où elle sert."
    )
    assert fin.mode == 0o644, f"Mode attendu 0644, vu : {oct(fin.mode)}"


# ─── Tâche 14 — Déploiement par vagues (serial) ─────────────────────────
def test_14_les_vagues_sont_reellement_sequencees(web1, web2):
    """Prouve `serial` par les horodatages de l'état posé, pas par le YAML.

    Le seul témoin observable d'un déploiement par vagues est le décalage entre
    les états qu'il pose : avec `serial: 1` et une stabilisation de 5 secondes,
    web1 est traité, on attend, puis web2. Sans séquencement, les deux copies
    partent dans le même lot et les mtimes tombent à quelques millisecondes
    l'un de l'autre (mesuré sur ce lab : les deux hôtes répondent à moins de
    10 ms d'écart, et dans un ordre qui change d'un run à l'autre).

    Le contenu des marqueurs est stable, donc leur mtime est celui de la vague
    qui les a créés et il ne bouge plus aux runs suivants : c'est le `setup.yaml`
    qui les efface, sans quoi on mesurerait l'écart d'un run précédent.

    La comparaison porte sur DEUX machines : elle ne vaut que si leurs horloges
    sont d'accord. On ne le suppose pas, on le mesure, sinon un décalage de
    quelques secondes suffirait à faire passer un run parallèle pour un
    déploiement par vagues.
    """
    f1 = web1.file("/tmp/lab100-vague-web1.lab.txt")
    f2 = web2.file("/tmp/lab100-vague-web2.lab.txt")
    assert f1.exists, "/tmp/lab100-vague-web1.lab.txt absent sur web1"
    assert f2.exists, "/tmp/lab100-vague-web2.lab.txt absent sur web2"

    # TROU T14 : l'énoncé impose « mode 0644, owner root » sur chaque marqueur
    # de vague, non vérifié jusqu'ici. Un marqueur posé par un `copy` sans
    # `mode:`/`owner:` hériterait de l'umask et du become-user, pas forcément
    # 0644/root. La solution les fixe explicitement.
    for f, nom in ((f1, "web1"), (f2, "web2")):
        assert f.mode == 0o644, (
            f"Le marqueur de vague de {nom} doit être en 0644 (tâche 14), vu : "
            f"{oct(f.mode)}."
        )
        assert f.user == "root", (
            f"Le marqueur de vague de {nom} doit appartenir à root (tâche 14), "
            f"vu : {f.user}."
        )

    # Décalage d'horloge entre les deux VMs, encadré : on lit web1, puis web2,
    # puis web1 à nouveau, et on compare web2 au milieu de l'intervalle. Le
    # temps de trajet des deux appels se compense ainsi de lui-même.
    avant = float(web1.check_output("date +%s.%N"))
    milieu = float(web2.check_output("date +%s.%N"))
    apres = float(web1.check_output("date +%s.%N"))
    decalage = milieu - (avant + apres) / 2
    assert abs(decalage) < 1.0, (
        f"Les horloges de web1 et web2 divergent de {decalage:.2f} s : la "
        "preuve du séquencement repose sur la comparaison de leurs mtimes, "
        "elle ne vaut plus rien. Vérifiez chronyd sur les deux VMs."
    )

    ecart = (f2.mtime - f1.mtime).total_seconds()
    assert ecart >= 3.0, (
        f"Les deux vagues sont séparées de {ecart:.0f} s seulement (web1 à "
        f"{f1.mtime}, web2 à {f2.mtime}).\n"
        "Les webservers ont été traités ensemble, pas en vagues successives : "
        "un déploiement parallèle pose les deux marqueurs à quelques "
        "millisecondes d'écart.\n"
        "L'énoncé impose un hôte à la fois et une stabilisation de 5 secondes "
        "entre les vagues : les deux mots-clés se placent au niveau du play."
    )


# ─── Tâche 15 — delegate_to / run_once ──────────────────────────────────
def test_15_le_journal_est_ecrit_sur_lhote_delegue(db1):
    """L'état doit apparaître sur db1, et une seule fois.

    Une ligne, pas deux : c'est la preuve de `run_once`. Sans lui, le play
    tournant sur deux webservers écrirait deux lignes dans le même journal (le
    module en ajoute une par hôte, chacune portant son propre
    `inventory_hostname`). Avec, seul le premier hôte de la vague écrit.

    La ligne doit nommer un WEBSERVER, pas db1 : `delegate_to` déplace
    l'exécution sans changer `inventory_hostname`. Elle doit aussi porter
    `worker_count`, qui est une variable du groupe webservers : un play qui
    ciblerait db1 en direct, sans déléguer, ne l'aurait pas.
    """
    journal = db1.file("/tmp/lab100-deploy-log.txt")
    assert journal.exists, (
        "/tmp/lab100-deploy-log.txt absent de db1.lab : la tâche n'a pas été "
        "déléguée, ou pas au bon hôte."
    )
    # TROU T15 : l'énoncé impose « mode 0644, owner root » sur le journal, non
    # vérifié. La solution les fixe (create + owner root + mode 0644) : un
    # lineinfile sans ces paramètres laisserait des droits dépendant de l'umask.
    assert journal.mode == 0o644, (
        f"Le journal doit être en 0644 (tâche 15), vu : {oct(journal.mode)}."
    )
    assert journal.user == "root", (
        f"Le journal doit appartenir à root (tâche 15), vu : {journal.user}."
    )
    lignes = [ln.strip() for ln in journal.content_string.splitlines() if ln.strip()]
    assert len(lignes) == 1, (
        f"Le journal doit contenir exactement une ligne, il en a {len(lignes)} :"
        f"\n{lignes}\n"
        "Deux lignes = la tâche a tourné une fois par webserver. Le mot-clé qui "
        "limite une tâche à une seule exécution par vague manque."
    )
    assert re.search(r"\bweb[12]\.lab\b", lignes[0]), (
        f"La ligne du journal doit nommer le webserver à l'origine du "
        f"déploiement, vu : {lignes[0]!r}\n"
        "Déléguer ne change pas l'hôte du play : `inventory_hostname` reste "
        "celui du webserver."
    )
    assert re.search(r"\b4\b", lignes[0]), (
        f"La ligne du journal doit porter la valeur de worker_count (4), vu : "
        f"{lignes[0]!r}"
    )


def test_15b_le_journal_napparait_sur_aucun_webserver(web1, web2):
    """Preuve par l'absence : déléguer, c'est agir AILLEURS.

    Un candidat qui oublierait `delegate_to` poserait le journal sur web1 et
    web2, et rien sur db1. L'assertion positive seule ne verrait pas la
    différence si db1 avait par ailleurs reçu le fichier.
    """
    for hote, nom in ((web1, "web1"), (web2, "web2")):
        assert not hote.file("/tmp/lab100-deploy-log.txt").exists, (
            f"/tmp/lab100-deploy-log.txt ne doit PAS exister sur {nom}.lab : le "
            "journal est centralisé sur db1, la tâche doit s'exécuter là-bas."
        )


# ─── Tâche 16 — Tâche planifiée ─────────────────────────────────────────
def test_16_la_tache_planifiee_est_dans_la_crontab_dappuser(db1):
    """Interroge le planificateur, pas un fichier posé à côté.

    `crontab -l -u appuser` rend ce que cron exécutera vraiment pour cet
    utilisateur. Lire /var/spool/cron/appuser avec `file()` donnerait le même
    texte mais prouverait moins : un fichier peut être là sans que crontab le
    reconnaisse (droits, propriétaire, nom).

    On refuse aussi le doublon : deux lignes pour le même job = un playbook non
    idempotent qui empile une entrée à chaque passage. C'est ce que le marqueur
    d'identité du module évite, et il est facile de l'oublier.
    """
    listing = db1.run("crontab -l -u appuser")
    assert listing.rc == 0, (
        "Aucune crontab pour appuser sur db1 (`crontab -l -u appuser` a "
        f"échoué) :\n{listing.stderr.strip()}"
    )
    lignes = [
        ln.strip() for ln in listing.stdout.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    jobs = [ln for ln in lignes if "lab100-rapport.log" in ln]
    assert len(jobs) == 1, (
        f"Exactement une entrée attendue pour le rapport, {len(jobs)} vue(s).\n"
        f"Crontab d'appuser :\n{listing.stdout.strip()}\n"
        "Plusieurs entrées identiques signifient que le playbook en rajoute "
        "une à chaque passage : il manque l'identifiant qui rend la tâche "
        "planifiée idempotente."
    )
    champs = jobs[0].split()
    assert champs[:5] == ["5", "4", "*", "*", "*"], (
        f"Horaire attendu « 5 4 * * * » (04h05 tous les jours), vu : "
        f"« {' '.join(champs[:5])} ».\nLigne complète : {jobs[0]!r}"
    )
    assert "/usr/bin/date" in jobs[0], (
        f"La commande planifiée doit être celle de l'énoncé, vue : {jobs[0]!r}"
    )


# ─── Tâche 17 — Tags ────────────────────────────────────────────────────
_MARQUEURS_TAGS = {
    "preparation": "/tmp/lab100-tag-preparation.txt",
    "deploiement": "/tmp/lab100-tag-deploiement.txt",
    "always": "/tmp/lab100-tag-always.txt",
    "purge": "/tmp/lab100-tag-purge.txt",
}


def test_17_les_tags_selectionnent_vraiment_les_taches(db1):
    """Prouve les tags par un VRAI run sélectif, et par ce qu'il pose ou non.

    Le conftest rejoue la solution sans `--tags` : ce run prouve déjà `never`
    (la purge ne doit pas avoir eu lieu), à condition que le `setup.yaml` ait
    effacé le marqueur au préalable, ce qu'il fait. Pour le reste, le test
    lance lui-même le playbook avec `--tags`, plutôt que de faire modifier le
    conftest pour un seul lab.

    Table rase d'abord : sans elle, les marqueurs laissés par le run du conftest
    rendraient les assertions positives vraies sans qu'aucune tâche n'ait
    tourné. C'est exactement le faux vert que ce dépôt traque.

    Les quatre assertions se tiennent ensemble : deux positives (le tag demandé
    tourne, `always` tourne quand même) et deux négatives (un tag non demandé ne
    tourne pas, `never` ne tourne toujours pas). Une seule des quatre serait
    facile à satisfaire par accident.
    """
    assert not db1.file(_MARQUEURS_TAGS["purge"]).exists, (
        "La purge a tourné alors que personne ne l'a demandée. Une tâche "
        "destructive doit être hors de portée d'un run ordinaire : il lui "
        "manque le tag qui l'exclut par défaut."
    )

    db1.check_output("sh -c 'rm -f /tmp/lab100-tag-*.txt'")
    for nom, chemin in _MARQUEURS_TAGS.items():
        assert not db1.file(chemin).exists, f"Table rase incomplète : {chemin}"

    res = _lancer_solution("--tags", "deploiement")
    assert res.returncode == 0, (
        "Le playbook doit se jouer proprement sous « --tags deploiement ».\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}"
    )

    try:
        assert db1.file(_MARQUEURS_TAGS["deploiement"]).exists, (
            "« --tags deploiement » n'a pas exécuté la tâche taguée "
            "`deploiement`."
        )
        assert db1.file(_MARQUEURS_TAGS["always"]).exists, (
            "La tâche systématique ne s'est pas exécutée sous « --tags "
            "deploiement ». Le tag qui force une tâche à tourner quel que soit "
            "le filtre est un tag réservé, il ne s'invente pas."
        )
        assert not db1.file(_MARQUEURS_TAGS["preparation"]).exists, (
            "La tâche taguée `preparation` a tourné sous « --tags deploiement » "
            ": le filtrage par tags ne fonctionne pas. Vérifiez que chaque "
            "marqueur porte son propre tag, et un seul."
        )
        assert not db1.file(_MARQUEURS_TAGS["purge"]).exists, (
            "La purge a tourné sous « --tags deploiement » alors qu'elle doit "
            "exiger une demande explicite."
        )
    finally:
        # Le run sélectif laisse le marqueur de préparation manquant : sans
        # cette restauration, le test d'idempotence qui suit verrait un
        # `changed` légitime et accuserait à tort la solution.
        _lancer_solution()

    assert db1.file(_MARQUEURS_TAGS["preparation"]).exists, (
        "Le run complet de restauration n'a pas reposé le marqueur de "
        "préparation."
    )


# ─── Tâche 18 — Facts personnalisés ─────────────────────────────────────
def test_18_le_fact_personnalise_remonte_vraiment(web1, web2):
    """Le fact doit REMONTER dans une collecte, pas simplement exister.

    On ne teste pas la présence de /etc/ansible/facts.d/lab100.fact : un fichier
    présent prouve qu'on sait faire un `copy`, pas qu'on sait poser un fact. Le
    fichier peut être là et ne rien produire, et c'est le cas le plus fréquent :
    posé exécutable, Ansible le LANCE et attend du JSON sur sa sortie standard ;
    un INI dans ce cas ne remonte pas du tout.

    On interroge donc `ansible -m setup` et on lit `ansible_local`, c'est-à-dire
    exactement ce qu'un playbook verrait. Les valeurs viennent des group_vars de
    la tâche 2 : les recopier en dur donnerait le même fichier, mais l'énoncé
    demande de publier ce que l'inventaire sait de l'hôte.
    """
    for hote in ("web1.lab", "web2.lab"):
        locaux = _facts_locaux(hote)
        assert "lab100" in locaux, (
            f"Aucun fact `lab100` sur {hote} (facts locaux vus : "
            f"{sorted(locaux) or 'aucun'}).\n"
            "Le fichier existe peut-être : ce test demande à Ansible ce qu'il "
            "en RÉCUPÈRE. Un fact qui ne remonte pas n'est pas un fact.\n"
            "Pistes : le nom du fichier (.fact), son emplacement, son format, "
            "et surtout son mode (un fact de données ne doit pas être "
            "exécutable, sinon Ansible essaie de l'exécuter)."
        )
        exam = locaux["lab100"].get("exam")
        assert exam is not None, (
            f"Le fact `lab100` de {hote} n'a pas de section `exam`, vu : "
            f"{locaux['lab100']}"
        )
        assert exam.get("env") == "production", (
            f"`lab100.exam.env` doit valoir la valeur de app_env "
            f"(« production ») sur {hote}, vu : {exam.get('env')!r}"
        )
        assert str(exam.get("workers")) == "4", (
            f"`lab100.exam.workers` doit valoir la valeur de worker_count (4) "
            f"sur {hote}, vu : {exam.get('workers')!r}"
        )


def test_11d_le_handler_redemarre_vraiment_nginx(web1):
    """Prouve le handler par le COMPORTEMENT, pas en lisant le YAML du rôle.

    test_11c lit la structure du rôle, en assumant qu'« un handler qui n'est
    jamais notifié ne laisse aucune trace ». C'est faux : il suffit de rendre
    le fichier déployé différent de son template. La tâche template rapporte
    alors `changed`, ce qui doit notifier le handler, qui doit redémarrer
    nginx. Si le handler manque, ou n'est pas notifié, ou ne redémarre rien,
    le PID de nginx ne bouge pas.

    Un rôle peut déclarer un handler parfait et ne jamais le notifier : la
    lecture du YAML est verte dans ce cas, ce test non.
    """
    avant = web1.check_output("systemctl show -p MainPID --value nginx")
    assert avant.strip() not in ("", "0"), (
        "nginx ne tourne pas sur web1 : impossible de prouver le handler."
    )

    web1.check_output(
        "sh -c \'echo divergence >> /usr/share/nginx/html/index.html\'"
    )
    replay_solution(__file__)

    apres = web1.check_output("systemctl show -p MainPID --value nginx")
    assert apres.strip() not in ("", "0"), (
        "nginx ne tourne plus après le rejeu : le handler l'a arrêté sans le "
        "relancer ?"
    )
    assert avant.strip() != apres.strip(), (
        "Le fichier déployé a été modifié, la tâche template a donc rapporté "
        "`changed`, mais nginx n'a PAS redémarré (PID inchangé : "
        f"{avant.strip()}).\n"
        "Soit la tâche template ne notifie aucun handler, soit le handler ne "
        "redémarre pas nginx. Déclarer un handler ne suffit pas : encore "
        "faut-il le notifier."
    )


# ─── Tâche 19 — Content Collection via requirements.yml ─────────────────────
def test_19_la_collection_est_installee_et_resolvable(db1):
    """La collection épinglée doit être RÉELLEMENT installée et résolvable.

    On ne se fie pas au requirements.yml (une intention), mais à la sortie de
    `ansible-galaxy collection list` déposée sur db1 : elle porte le FQCN et la
    version réellement résolue dans le chemin d'installation du projet. Un
    requirements.yml correct mais jamais installé ne laisse aucune trace ici.

    On exige la version ÉPINGLÉE (10.5.0), pas seulement la présence de
    community.general : la formation impose le pinning semver strict, et le
    système embarque d'autres versions de la collection. Voir 10.5.0 dans la
    preuve prouve que c'est bien le requirements.yml qui a piloté l'installation,
    et pas la collection déjà présente sur la machine.
    """
    preuve = db1.file("/tmp/lab100-collections.txt")
    assert preuve.exists, (
        "/tmp/lab100-collections.txt absent : la collection n'a pas été "
        "installée depuis un requirements.yml, ou l'inventaire des collections "
        "installées n'a pas été déposé sur db1 (tâche 19)."
    )
    assert preuve.mode == 0o644, f"Mode attendu 0644, vu : {oct(preuve.mode)}"
    assert preuve.user == "root", f"Propriétaire attendu root, vu : {preuve.user}"
    contenu = preuve.content_string
    assert "community.general" in contenu, (
        "La preuve d'installation ne mentionne pas community.general : "
        f"`ansible-galaxy collection list` ne l'a pas résolue.\n{contenu[:400]}"
    )
    assert "10.5.0" in contenu, (
        "La version épinglée 10.5.0 n'apparaît pas dans l'inventaire des "
        "collections : le requirements.yml n'a pas installé la version demandée "
        f"(pinning semver strict exigé).\n{contenu[:400]}"
    )


def test_19b_un_module_de_la_collection_a_ete_utilise(db1):
    """Prouve l'USAGE de la collection par l'état qu'un de ses modules a posé.

    Installer une collection ne suffit pas : l'objectif EX294 est de « s'en
    servir dans un playbook ». community.general.ini_file est un module fourni
    par la collection installée ; son effet se lit dans le fichier INI qu'il
    écrit sur db1. Un fichier obtenu par un simple `copy` de builtin ne
    prouverait pas qu'on sait utiliser un module de collection : on vérifie donc
    la structure INI que seul ce module produit (section + clé = valeur).
    """
    usage = db1.file("/tmp/lab100-collection-use.ini")
    assert usage.exists, (
        "/tmp/lab100-collection-use.ini absent : aucun module de la collection "
        "installée n'a été utilisé (tâche 19)."
    )
    assert usage.mode == 0o644, f"Mode attendu 0644, vu : {oct(usage.mode)}"
    assert usage.user == "root", f"Propriétaire attendu root, vu : {usage.user}"
    contenu = usage.content_string
    assert "[collections]" in contenu, (
        "Le fichier INI produit par community.general.ini_file doit porter la "
        f"section [collections] (tâche 19).\nContenu : {contenu.strip()[:200]}"
    )
    assert re.search(r"^\s*installed\s*=\s*community\.general\s*$", contenu, re.M), (
        "La section [collections] doit contenir « installed = community.general "
        "», la clé que community.general.ini_file a écrite depuis la collection "
        f"installée.\nContenu : {contenu.strip()[:200]}"
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)


# ----------------------------------------------------------------------
# La preuve de persistance. Volontairement en DERNIER : il redémarre les VMs.
# ----------------------------------------------------------------------


@pytest.mark.slow
def test_99_persistance_reelle_apres_reboot():
    """Redémarre web1 et db1, puis re-vérifie l'état RUNTIME.

    Les tests 08b, 09c et 10b s'appuient sur des indices de persistance : la
    colonne « persistant » de `semanage boolean -l`, `firewall-cmd
    --permanent`, une entrée dans /etc/fstab. Ce sont de bons indices, et ils
    valent mieux que rien, mais aucun ne PROUVE que la machine revient
    correcte : un fstab syntaxiquement valide peut faire échouer le boot, une
    règle permanente peut être masquée par une zone active différente, un
    volume logique peut ne pas être activé au démarrage.

    La persistance est LE piège qui fait échouer les candidats RHCE. Un
    capstone qui la certifie sans jamais redémarrer certifie une hypothèse.
    Ce test la transforme en fait.
    """
    web1 = reboot_and_wait("web1.lab")
    db1 = reboot_and_wait("db1.lab")

    # Tâche 8 : le booléen doit être ON au runtime, après redémarrage.
    out = web1.check_output("getsebool httpd_can_network_connect")
    valeur = out.split("-->")[-1].strip()
    assert valeur == "on", (
        "Après reboot, httpd_can_network_connect est retombé à "
        f"« {valeur} » : setsebool a été utilisé sans -P. C'est l'erreur qui "
        "coûte les points à l'examen, et que getsebool seul ne montre pas."
    )

    # Tâche 9 : les services doivent être ouverts au runtime, après redémarrage.
    for hote, nom in ((web1, "web1"), (db1, "db1")):
        actifs = hote.check_output("firewall-cmd --list-services")
        attendus = ("http", "https") if nom == "web1" else ("mysql",)
        for svc in attendus:
            assert svc in actifs.split(), (
                f"Après reboot, {svc} n'est plus ouvert sur {nom} (services "
                f"actifs : {actifs.strip()}). La règle n'a pas survécu, ou la "
                "zone active n'est pas celle qui la porte."
            )

    # Tâche 10 : le montage LVM doit être remonté par le système, seul.
    monte = db1.run("findmnt --noheadings --target /mnt/data")
    assert monte.rc == 0, (
        "Après reboot, /mnt/data n'est plus monté : l'entrée fstab est absente, "
        "fausse, ou le volume logique n'est pas activé au démarrage.\n"
        "C'est exactement le scénario que la tâche 10 cherche à prévenir : la "
        "machine était correcte à l'instant T, elle est fausse au redémarrage."
    )

    # Le service doit revenir seul : `enabled` sans reboot ne le prouve pas.
    assert web1.service("nginx").is_running, (
        "Après reboot, nginx ne tourne plus sur web1 : le service a été démarré "
        "sans être activé (`enabled: true`)."
    )

    # Tâche 16 : une tâche planifiée qui ne survit pas au redémarrage ne sert à
    # rien. On revérifie l'entrée ET le démon qui l'exécutera : une crontab
    # intacte sous un crond éteint ne déclenchera jamais.
    listing = db1.run("crontab -l -u appuser")
    assert listing.rc == 0 and "lab100-rapport.log" in listing.stdout, (
        "Après reboot, la tâche planifiée d'appuser a disparu.\n"
        f"Crontab vue :\n{listing.stdout.strip() or '(vide)'}"
    )
    assert db1.service("crond").is_running, (
        "Après reboot, crond ne tourne plus sur db1 : la tâche planifiée est "
        "bien écrite, et ne partira jamais."
    )

    # Tâche 18 : le fact doit remonter sur une machine qui vient de démarrer,
    # pas seulement sur celle où le playbook vient de passer.
    locaux = _facts_locaux("web1.lab")
    assert "lab100" in locaux, (
        "Après reboot, le fact `lab100` ne remonte plus sur web1 (facts locaux "
        f"vus : {sorted(locaux) or 'aucun'}). Un fact posé dans un répertoire "
        "volatil disparaît au redémarrage."
    )
