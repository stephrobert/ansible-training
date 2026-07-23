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
    REPO_ROOT, lab_host, lab_playbook, lab_solution_text, lab_inventory_args,
    assert_idempotent, reboot_and_wait, replay_solution, _EXTRA_ARGS, _roles_path,
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
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env)


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
    )
    assert res.returncode == 0, (
        f"La collecte de facts a échoué sur {hote} :\n"
        f"--- stdout ---\n{res.stdout.strip()}\n"
        f"--- stderr ---\n{res.stderr.strip()}"
    )
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
    """L'inventaire doit déclarer les deux groupes ET joindre leurs hôtes."""
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
        ("frontends", ("web1.lab", "web2.lab")),
        ("backends", ("db1.lab",)),
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
def test_02_variables_precedence(web1):
    """Tâche 2 : group_vars + host_vars correctement résolus."""
    f = web1.file("/tmp/lab200-vars.txt")
    assert f.exists, "Le playbook doit déposer /tmp/lab200-vars.txt sur web1"
    content = f.content_string
    assert "staging" in content, "deploy_stage doit valoir 'staging'"
    assert "pool_size: 8" in content or "pool_size = 8" in content


# ─── Tâche 3 — Vault ─────────────────────────────────────────────────────
def test_03_vault_decrypted(db1):
    f = db1.file("/tmp/lab200-token.txt")
    assert f.exists, "/tmp/lab200-token.txt absent — vars_files vault.yml KO"
    assert f.mode == 0o600, f"Mode attendu 0600, vu : {oct(f.mode)}"
    assert "Ex294-Deux" in f.content_string, "api_token déchiffré attendu"


# ─── Tâche 4 — Templates et fichiers ────────────────────────────────────
def test_04_template_service_conf(db1):
    f = db1.file("/tmp/lab200-service.conf")
    assert f.exists
    assert f.mode == 0o600, f"Mode attendu 0600, vu : {oct(f.mode)}"
    assert f.user == "svcuser"
    assert f.group == "svcgroup"
    content = f.content_string
    assert "lab200schema" in content, "schema_name doit apparaître"
    # Le rendu doit contenir le nom d'hôte Ansible (« db1 » sur db1.lab), preuve
    # qu'il est rendu PAR HÔTE et non figé.
    assert re.search(r"\bdb1\b", content), (
        "Le rendu de /tmp/lab200-service.conf doit contenir le nom d'hôte Ansible "
        f"(« db1 » sur db1.lab), absent du contenu :\n{content.strip()[:200]}\n"
        "Sans lui, ce n'est pas un template rendu par hôte."
    )


# ─── Tâche 5 — Paquets ──────────────────────────────────────────────────
def test_05_packages_installed(db1, web1, web2):
    assert db1.package("httpd").is_installed
    assert db1.package("valkey").is_installed
    assert db1.package("python3-libselinux").is_installed
    # python3-libselinux est exigé « sur TOUS les hôtes » : sur les frontends,
    # c'est ce paquet qui fournit les liaisons Python dont
    # ansible.posix.seboolean a besoin (tâche 8).
    for host, nom in ((web1, "web1"), (web2, "web2")):
        assert host.package("python3-libselinux").is_installed, (
            f"python3-libselinux doit être installé sur {nom}.lab : l'énoncé "
            "l'exige sur tous les hôtes."
        )


# ─── Tâche 6 — Services ─────────────────────────────────────────────────
def test_06_services_running(web1, db1):
    assert web1.service("httpd").is_running, "httpd KO sur web1"
    assert web1.service("httpd").is_enabled
    assert db1.service("valkey").is_running, "valkey KO sur db1"
    # « démarrés ET activés au boot » : les deux moitiés de l'exigence sont
    # testées, pour httpd comme pour valkey.
    assert db1.service("valkey").is_enabled, (
        "valkey tourne sur db1 mais n'est pas activé au boot : il ne reviendrait "
        "pas après un redémarrage (tâche 6)."
    )


# ─── Tâche 7 — Utilisateurs ─────────────────────────────────────────────
def test_07_user_svcuser(db1):
    user = db1.user("svcuser")
    assert user.exists
    assert user.uid == 3200
    assert user.group == "svcgroup"
    assert user.shell == "/bin/bash", (
        f"svcuser doit avoir le shell /bin/bash (tâche 7), vu : {user.shell!r}."
    )
    grp = db1.group("svcgroup")
    assert grp.exists
    assert grp.gid == 3200


def test_07b_svcuser_sudo_journalctl_nopasswd(db1):
    """svcuser doit lancer journalctl en sudo SANS mot de passe, et RIEN d'autre.

    L'énoncé l'exige explicitement (« uniquement cette commande »). On interroge
    la politique sudo effective plutôt que le fichier : c'est l'état réel qui
    compte, peu importe où la règle est écrite.
    """
    allowed = db1.run("sudo -l -U svcuser 2>/dev/null")
    assert allowed.rc == 0, (
        "Impossible de lire la politique sudo de svcuser (sudo -l -U svcuser)."
    )
    out = allowed.stdout
    assert "NOPASSWD" in out and "/usr/bin/journalctl" in out, (
        "svcuser doit pouvoir exécuter /usr/bin/journalctl en sudo sans mot de "
        f"passe.\nPolitique vue :\n{out.strip()}\n"
        "Déclarez la règle dans /etc/sudoers.d/ (validée par visudo -cf)."
    )
    # « uniquement cette commande » : un blanc-seing est une faute de sécurité.
    assert not re.search(r"NOPASSWD:\s*ALL\b", out), (
        "svcuser a un sudo NOPASSWD sur TOUTES les commandes.\n"
        f"Politique vue :\n{out.strip()}\n"
        "L'énoncé demande uniquement /usr/bin/journalctl : restreignez la règle."
    )


# ─── Tâche 8 — SELinux ──────────────────────────────────────────────────
def test_08_selinux_httpd_can_network_connect_db(web1):
    """Le booléen doit être actif dans le noyau, ici et maintenant."""
    cmd = web1.run("getsebool httpd_can_network_connect_db")
    assert cmd.rc == 0, f"getsebool a échoué : {cmd.stderr.strip()}"
    value = cmd.stdout.rsplit("-->", 1)[-1].strip()
    assert value == "on", (
        f"httpd_can_network_connect_db doit être activé, vu : {value or '?'}\n"
        f"Sortie complète : {cmd.stdout.strip()}"
    )


def test_08b_selinux_boolean_persistent(web1):
    """Le booléen doit survivre au reboot (SELinux : valeur « persistent »).

    `setsebool` sans -P ne tient que jusqu'au redémarrage : c'est l'erreur
    classique qui fait perdre les points à l'examen.
    """
    cmd = web1.run("semanage boolean -l | grep '^httpd_can_network_connect_db'")
    assert cmd.rc == 0, (
        "Impossible de lire la valeur persistante du booléen "
        "(semanage boolean -l)."
    )
    assert re.search(r"\(\s*on\s*,\s*on\s*\)", cmd.stdout), (
        "httpd_can_network_connect_db doit être activé DE FAÇON PERSISTANTE.\n"
        f"Vu : {cmd.stdout.strip()}\n"
        "Le second champ est la valeur au prochain boot : elle doit être « on ». "
        "Le module ansible.posix.seboolean prend un paramètre pour cela."
    )


# ─── Tâche 9 — Firewalld ────────────────────────────────────────────────
def test_09_firewall_http_https_open(web1):
    cmd = web1.run("firewall-cmd --list-services")
    assert "http" in cmd.stdout
    assert "https" in cmd.stdout


def test_09b_firewall_valkey_port_db1(db1):
    cmd = db1.run("firewall-cmd --list-ports")
    assert "6379/tcp" in cmd.stdout, (
        "Le port 6379/tcp (valkey) doit être ouvert sur db1 (vu : "
        f"{cmd.stdout.strip()})."
    )


def test_09c_firewall_rules_are_permanent(web1, db1):
    """Les règles doivent être dans la configuration PERMANENTE, pas seulement
    dans le runtime.

    `firewall-cmd --add-service=http` sans --permanent est perdu au reboot.
    `--list-services`/`--list-ports` seul ne voit que le runtime.
    """
    out = web1.run("firewall-cmd --permanent --list-services")
    for svc in ("http", "https"):
        assert svc in out.stdout, (
            f"Le service {svc} doit être ouvert de façon PERMANENTE sur web1 "
            f"(vu en permanent : {out.stdout.strip()}).\n"
            "Une règle runtime disparaît au redémarrage."
        )
    out = db1.run("firewall-cmd --permanent --list-ports")
    assert "6379/tcp" in out.stdout, (
        "Le port 6379/tcp doit être ouvert de façon PERMANENTE sur db1 "
        f"(vu en permanent : {out.stdout.strip()})."
    )


# ─── Tâche 10 — Stockage ────────────────────────────────────────────────
def test_10_lvm_ext4_mounted(db1):
    mount = db1.mount_point("/srv/appdata")
    assert mount.exists, "/srv/appdata doit être monté"
    assert mount.filesystem == "ext4"


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
    assert line is not None, (
        "Aucune entrée /srv/appdata active dans /etc/fstab : le montage ne "
        "survivra pas au reboot.\n"
        "Le module ansible.posix.mount écrit dans fstab avec state=mounted."
    )
    assert "ext4" in line, (
        f"L'entrée fstab de /srv/appdata doit être en ext4 (vu : {line.strip()})."
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
    assert "lv_app" in tailles, (
        f"Aucun LV nommé « lv_app » dans vg_lab (vus : {sorted(tailles) or 'aucun'}).\n"
        "L'énoncé impose ce nom exact."
    )
    taille = tailles["lv_app"]
    assert abs(taille - 400.0) <= 16.0, (
        f"lv_app doit faire ~400 Mo, mesuré : {taille:.0f} Mo.\n"
        "La taille est un critère de la tâche 10, au même titre que le montage."
    )


# ─── Tâche 11 — Rôle web_publish ────────────────────────────────────────
def test_11_role_index_html(web1, web2):
    for host in (web1, web2):
        f = host.file("/var/www/html/index.html")
        assert f.exists, f"index.html absent sur {host.system_info.hostname}"


def test_11b_template_contient_le_hostname(web1, web2):
    """Le template doit produire un contenu PAR HÔTE, pas un fichier statique."""
    for host, name in ((web1, "web1"), (web2, "web2")):
        content = host.file("/var/www/html/index.html").content_string
        assert name in content, (
            f"index.html sur {name}.lab ne contient pas son nom d'hôte "
            f"d'inventaire.\nContenu : {content.strip()[:200]}\n"
            "Le template doit être rendu par hôte (inventory_hostname)."
        )


def test_11c_role_declare_un_handler(web1):
    """Le rôle doit déclarer un handler notifié par la tâche de template.

    Un handler qui n'est jamais notifié ne laisse aucune trace dans l'état final,
    donc testinfra ne peut pas le voir. On contrôle donc la STRUCTURE du rôle.
    """
    handlers = _role_file("handlers/main.yml")
    if handlers is None:
        handlers = _role_file("handlers/main.yaml")
    assert handlers is not None, (
        "Le rôle web_publish doit déclarer un handler dans "
        "labs/rhce/mock-ex294-2/roles/web_publish/handlers/main.yml (absent)."
    )
    names = {h.get("name", "") for h in handlers if isinstance(h, dict)}
    assert any("httpd" in n.lower() for n in names), (
        "Aucun handler concernant httpd dans le rôle web_publish "
        f"(handlers vus : {sorted(names) or 'aucun'})."
    )

    tasks = _role_file("tasks/main.yml")
    if tasks is None:
        tasks = _role_file("tasks/main.yaml")
    assert tasks is not None, "Le rôle web_publish doit avoir tasks/main.yml."
    notifying = [
        t for t in tasks
        if isinstance(t, dict) and t.get("notify")
        and any(k.endswith("template") for k in t)
    ]
    assert notifying, (
        "La tâche qui déploie le template doit notifier le handler "
        "(mot-clé `notify:`). Sans notification, le handler ne tourne jamais et "
        "httpd ne relit pas sa configuration."
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
        assert f.exists, f"/tmp/slot{n} absent"
        content = f.content_string
        assert re.search(rf"\b{parity}\b", content), (
            f"/tmp/slot{n} doit contenir le mot '{parity}', vu : "
            f"{content.strip()[:50]!r}\n"
            "La condition de parité doit porter sur le numéro du fichier."
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
    assert len(cibles) == 1, (
        f"La tâche 12 doit créer /tmp/slot1..6 en UNE SEULE tâche (avec une "
        f"boucle), or {len(cibles)} tâche(s) créent ces fichiers.\n"
        "Six tâches séparées produisent le même état mais violent l'énoncé."
    )
    unique = cibles[0]
    assert any(cle in unique for cle in ("loop", "with_items", "with_sequence")), (
        "La tâche qui crée les 6 fichiers doit porter une boucle (`loop:`).\n"
        f"Clés de la tâche vue : {sorted(unique)}"
    )


# ─── Tâche 13 — block / rescue / always ─────────────────────────────────
@pytest.fixture(scope="module")
def run_complet():
    """Un run complet du playbook, dont on garde la sortie brute.

    Le PLAY RECAP est le seul endroit où l'on peut lire `rescued` et `ignored`.
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
    """Prouve le rescue par les compteurs du PLAY RECAP, pas par le YAML."""
    recap = _recap_de(run_complet, "db1.lab")
    assert recap.get("rescued", 0) >= 1, (
        "Aucun rescue n'a été déclenché sur db1 (rescued="
        f"{recap.get('rescued', 0)}).\n"
        "La tâche du block doit échouer POUR DE VRAI et le rescue doit la "
        "rattraper.\n"
        f"RECAP db1 : {recap}"
    )
    assert recap.get("ignored", 0) == 0, (
        f"db1 rapporte ignored={recap.get('ignored')} : une erreur a été mise "
        "sous le tapis avec `ignore_errors` au lieu d'être traitée par un "
        "`rescue`.\n"
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
    dans un `rescue`.
    """
    incident = db1.file("/tmp/lab200-incident.txt")
    assert incident.exists, (
        "/tmp/lab200-incident.txt absent : le rescue n'a pas consigné l'incident."
    )
    assert incident.mode == 0o644, f"Mode attendu 0644, vu : {oct(incident.mode)}"
    lignes = [ln.strip() for ln in incident.content_string.splitlines() if ln.strip()]
    assert "Lancer l'agent lab200" in lignes, (
        "/tmp/lab200-incident.txt doit contenir le nom de la tâche qui a échoué, "
        "tel qu'Ansible le rapporte, sur une ligne à lui.\n"
        f"Lignes vues : {lignes}\n"
        "La variable qui le porte n'est disponible que dans un `rescue`."
    )

    fin = db1.file("/tmp/lab200-incident-fin.txt")
    assert fin.exists, (
        "/tmp/lab200-incident-fin.txt absent : la section qui doit s'exécuter "
        "dans TOUS les cas ne l'a pas fait, alors que le bloc a justement échoué."
    )
    assert fin.mode == 0o644, f"Mode attendu 0644, vu : {oct(fin.mode)}"


# ─── Tâche 14 — Déploiement par vagues (serial) ─────────────────────────
def test_14_les_vagues_sont_reellement_sequencees(web1, web2):
    """Prouve `serial` par les horodatages de l'état posé, pas par le YAML.

    Avec `serial: 1` et une stabilisation de 6 secondes, web1 est traité, on
    attend, puis web2. Sans séquencement, les deux copies partent dans le même
    lot et les mtimes tombent à quelques millisecondes l'un de l'autre.
    """
    f1 = web1.file("/tmp/lab200-palier-web1.lab.txt")
    f2 = web2.file("/tmp/lab200-palier-web2.lab.txt")
    assert f1.exists, "/tmp/lab200-palier-web1.lab.txt absent sur web1"
    assert f2.exists, "/tmp/lab200-palier-web2.lab.txt absent sur web2"

    for f, nom in ((f1, "web1"), (f2, "web2")):
        assert f.mode == 0o644, (
            f"Le marqueur de palier de {nom} doit être en 0644 (tâche 14), vu : "
            f"{oct(f.mode)}."
        )
        assert f.user == "root", (
            f"Le marqueur de palier de {nom} doit appartenir à root (tâche 14), "
            f"vu : {f.user}."
        )

    # Décalage d'horloge entre les deux VMs, encadré.
    avant = float(web1.check_output("date +%s.%N"))
    milieu = float(web2.check_output("date +%s.%N"))
    apres = float(web1.check_output("date +%s.%N"))
    decalage = milieu - (avant + apres) / 2
    assert abs(decalage) < 1.0, (
        f"Les horloges de web1 et web2 divergent de {decalage:.2f} s : la preuve "
        "du séquencement repose sur la comparaison de leurs mtimes. Vérifiez "
        "chronyd sur les deux VMs."
    )

    ecart = (f2.mtime - f1.mtime).total_seconds()
    assert ecart >= 3.0, (
        f"Les deux vagues sont séparées de {ecart:.0f} s seulement (web1 à "
        f"{f1.mtime}, web2 à {f2.mtime}).\n"
        "Les frontends ont été traités ensemble, pas en vagues successives.\n"
        "L'énoncé impose un hôte à la fois et une stabilisation de 6 secondes "
        "entre les vagues."
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
    assert journal.exists, (
        "/tmp/lab200-central-log.txt absent de db1.lab : la tâche n'a pas été "
        "déléguée, ou pas au bon hôte."
    )
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
        "Deux lignes = la tâche a tourné une fois par frontend. Le mot-clé qui "
        "limite une tâche à une seule exécution par vague manque."
    )
    assert re.search(r"\bweb[12]\.lab\b", lignes[0]), (
        f"La ligne du journal doit nommer le frontend à l'origine du "
        f"déploiement, vu : {lignes[0]!r}\n"
        "Déléguer ne change pas l'hôte du play : `inventory_hostname` reste "
        "celui du frontend."
    )
    assert re.search(r"\b8\b", lignes[0]), (
        f"La ligne du journal doit porter la valeur de pool_size (8), vu : "
        f"{lignes[0]!r}"
    )


def test_15b_le_journal_napparait_sur_aucun_frontend(web1, web2):
    """Preuve par l'absence : déléguer, c'est agir AILLEURS."""
    for hote, nom in ((web1, "web1"), (web2, "web2")):
        assert not hote.file("/tmp/lab200-central-log.txt").exists, (
            f"/tmp/lab200-central-log.txt ne doit PAS exister sur {nom}.lab : le "
            "journal est centralisé sur db1, la tâche doit s'exécuter là-bas."
        )


# ─── Tâche 16 — Tâche planifiée ─────────────────────────────────────────
def test_16_la_tache_planifiee_est_dans_la_crontab_de_svcuser(db1):
    """Interroge le planificateur, pas un fichier posé à côté.

    `crontab -l -u svcuser` rend ce que cron exécutera vraiment. On refuse aussi
    le doublon : deux lignes pour le même job = un playbook non idempotent.
    """
    listing = db1.run("crontab -l -u svcuser")
    assert listing.rc == 0, (
        "Aucune crontab pour svcuser sur db1 (`crontab -l -u svcuser` a "
        f"échoué) :\n{listing.stderr.strip()}"
    )
    lignes = [
        ln.strip() for ln in listing.stdout.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    jobs = [ln for ln in lignes if "lab200-audit.log" in ln]
    assert len(jobs) == 1, (
        f"Exactement une entrée attendue pour le rapport, {len(jobs)} vue(s).\n"
        f"Crontab de svcuser :\n{listing.stdout.strip()}\n"
        "Plusieurs entrées identiques signifient que le playbook en rajoute une à "
        "chaque passage : il manque l'identifiant qui rend la tâche idempotente."
    )
    champs = jobs[0].split()
    assert champs[:5] == ["30", "22", "*", "*", "*"], (
        f"Horaire attendu « 30 22 * * * » (22h30 tous les jours), vu : "
        f"« {' '.join(champs[:5])} ».\nLigne complète : {jobs[0]!r}"
    )
    assert "/usr/bin/date" in jobs[0], (
        f"La commande planifiée doit être celle de l'énoncé, vue : {jobs[0]!r}"
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
    assert not db1.file(_MARQUEURS_TAGS["purge"]).exists, (
        "La purge a tourné alors que personne ne l'a demandée. Une tâche "
        "destructive doit être hors de portée d'un run ordinaire : il lui manque "
        "le tag qui l'exclut par défaut."
    )

    db1.check_output("sh -c 'rm -f /tmp/lab200-tag-*.txt'")
    for nom, chemin in _MARQUEURS_TAGS.items():
        assert not db1.file(chemin).exists, f"Table rase incomplète : {chemin}"

    res = _lancer_solution("--tags", "publish")
    assert res.returncode == 0, (
        "Le playbook doit se jouer proprement sous « --tags publish ».\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n"
        f"--- stderr ---\n{res.stderr[-2000:]}"
    )

    try:
        assert db1.file(_MARQUEURS_TAGS["publish"]).exists, (
            "« --tags publish » n'a pas exécuté la tâche taguée `publish`."
        )
        assert db1.file(_MARQUEURS_TAGS["always"]).exists, (
            "La tâche systématique ne s'est pas exécutée sous « --tags publish ». "
            "Le tag qui force une tâche à tourner quel que soit le filtre est un "
            "tag réservé, il ne s'invente pas."
        )
        assert not db1.file(_MARQUEURS_TAGS["init"]).exists, (
            "La tâche taguée `init` a tourné sous « --tags publish » : le "
            "filtrage par tags ne fonctionne pas. Vérifiez que chaque marqueur "
            "porte son propre tag, et un seul."
        )
        assert not db1.file(_MARQUEURS_TAGS["purge"]).exists, (
            "La purge a tourné sous « --tags publish » alors qu'elle doit exiger "
            "une demande explicite."
        )
    finally:
        # Le run sélectif laisse le marqueur d'init manquant : sans cette
        # restauration, le test d'idempotence verrait un `changed` légitime.
        _lancer_solution()

    assert db1.file(_MARQUEURS_TAGS["init"]).exists, (
        "Le run complet de restauration n'a pas reposé le marqueur d'init."
    )


# ─── Tâche 18 — Facts personnalisés ─────────────────────────────────────
def test_18_le_fact_personnalise_remonte_vraiment(web1, web2):
    """Le fact doit REMONTER dans une collecte, pas simplement exister.

    On interroge `ansible -m setup` et on lit `ansible_local`. Les valeurs
    viennent des group_vars de la tâche 2.
    """
    for hote in ("web1.lab", "web2.lab"):
        locaux = _facts_locaux(hote)
        assert "lab200" in locaux, (
            f"Aucun fact `lab200` sur {hote} (facts locaux vus : "
            f"{sorted(locaux) or 'aucun'}).\n"
            "Un fact qui ne remonte pas n'est pas un fact.\n"
            "Pistes : le nom du fichier (.fact), son emplacement, son format, et "
            "surtout son mode (un fact de données ne doit pas être exécutable)."
        )
        audit = locaux["lab200"].get("audit")
        assert audit is not None, (
            f"Le fact `lab200` de {hote} n'a pas de section `audit`, vu : "
            f"{locaux['lab200']}"
        )
        assert audit.get("stage") == "staging", (
            f"`lab200.audit.stage` doit valoir la valeur de deploy_stage "
            f"(« staging ») sur {hote}, vu : {audit.get('stage')!r}"
        )
        assert str(audit.get("pool")) == "8", (
            f"`lab200.audit.pool` doit valoir la valeur de pool_size (8) sur "
            f"{hote}, vu : {audit.get('pool')!r}"
        )


def test_11d_le_handler_redemarre_vraiment_httpd(web1):
    """Prouve le handler par le COMPORTEMENT, pas en lisant le YAML du rôle.

    On rend le fichier déployé différent de son template : la tâche template
    rapporte alors `changed`, ce qui doit notifier le handler, qui doit
    redémarrer httpd. Si le handler manque, le PID de httpd ne bouge pas.
    """
    avant = web1.check_output("systemctl show -p MainPID --value httpd")
    assert avant.strip() not in ("", "0"), (
        "httpd ne tourne pas sur web1 : impossible de prouver le handler."
    )

    web1.check_output(
        "sh -c 'echo divergence >> /var/www/html/index.html'"
    )
    replay_solution(__file__)

    apres = web1.check_output("systemctl show -p MainPID --value httpd")
    assert apres.strip() not in ("", "0"), (
        "httpd ne tourne plus après le rejeu : le handler l'a arrêté sans le "
        "relancer ?"
    )
    assert avant.strip() != apres.strip(), (
        "Le fichier déployé a été modifié, la tâche template a donc rapporté "
        f"`changed`, mais httpd n'a PAS redémarré (PID inchangé : {avant.strip()}).\n"
        "Soit la tâche template ne notifie aucun handler, soit le handler ne "
        "redémarre pas httpd."
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
    assert preuve.exists, (
        "/tmp/lab200-collections.txt absent : la collection n'a pas été installée "
        "depuis un requirements.yml, ou l'inventaire n'a pas été déposé sur db1."
    )
    assert preuve.mode == 0o644, f"Mode attendu 0644, vu : {oct(preuve.mode)}"
    assert preuve.user == "root", f"Propriétaire attendu root, vu : {preuve.user}"
    contenu = preuve.content_string
    assert "ansible.posix" in contenu, (
        "La preuve d'installation ne mentionne pas ansible.posix : "
        f"`ansible-galaxy collection list` ne l'a pas résolue.\n{contenu[:400]}"
    )
    assert "1.6.2" in contenu, (
        "La version épinglée 1.6.2 n'apparaît pas dans l'inventaire des "
        "collections : le requirements.yml n'a pas installé la version demandée "
        f"(pinning semver strict exigé).\n{contenu[:400]}"
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
    assert conf.exists, (
        "/etc/sysctl.d/99-lab200-collection.conf absent : aucun module de la "
        "collection installée n'a écrit le paramètre sysctl (tâche 19)."
    )
    contenu = conf.content_string
    assert re.search(r"vm\.swappiness\s*=\s*25", contenu), (
        "Le fichier sysctl doit porter « vm.swappiness = 25 » (tâche 19).\n"
        f"Contenu : {contenu.strip()[:200]}"
    )
    live = db1.run("sysctl -n vm.swappiness")
    assert live.rc == 0 and live.stdout.strip() == "25", (
        "vm.swappiness doit valoir 25 sur la machine (module ansible.posix.sysctl "
        f"appliqué), vu : {live.stdout.strip()!r}.\n"
        "Un fichier sysctl écrit sans être appliqué ne prouve pas l'usage du "
        "module de collection."
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
    assert valeur == "on", (
        "Après reboot, httpd_can_network_connect_db est retombé à "
        f"« {valeur} » : setsebool a été utilisé sans -P."
    )

    # Tâche 9 : les règles doivent être ouvertes au runtime, après redémarrage.
    services_web1 = web1.check_output("firewall-cmd --list-services")
    for svc in ("http", "https"):
        assert svc in services_web1.split(), (
            f"Après reboot, {svc} n'est plus ouvert sur web1 (services actifs : "
            f"{services_web1.strip()})."
        )
    ports_db1 = db1.check_output("firewall-cmd --list-ports")
    assert "6379/tcp" in ports_db1.split(), (
        f"Après reboot, 6379/tcp n'est plus ouvert sur db1 (ports actifs : "
        f"{ports_db1.strip()})."
    )

    # Tâche 10 : le montage LVM doit être remonté par le système, seul.
    monte = db1.run("findmnt --noheadings --target /srv/appdata")
    assert monte.rc == 0, (
        "Après reboot, /srv/appdata n'est plus monté : l'entrée fstab est "
        "absente, fausse, ou le volume logique n'est pas activé au démarrage."
    )

    # Le service doit revenir seul : `enabled` sans reboot ne le prouve pas.
    assert web1.service("httpd").is_running, (
        "Après reboot, httpd ne tourne plus sur web1 : le service a été démarré "
        "sans être activé (`enabled: true`)."
    )

    # Tâche 16 : la tâche planifiée doit survivre, et crond doit tourner.
    listing = db1.run("crontab -l -u svcuser")
    assert listing.rc == 0 and "lab200-audit.log" in listing.stdout, (
        "Après reboot, la tâche planifiée de svcuser a disparu.\n"
        f"Crontab vue :\n{listing.stdout.strip() or '(vide)'}"
    )
    assert db1.service("crond").is_running, (
        "Après reboot, crond ne tourne plus sur db1 : la tâche planifiée est "
        "bien écrite, et ne partira jamais."
    )

    # Tâche 18 : le fact doit remonter sur une machine qui vient de démarrer.
    locaux = _facts_locaux("web1.lab")
    assert "lab200" in locaux, (
        "Après reboot, le fact `lab200` ne remonte plus sur web1 (facts locaux "
        f"vus : {sorted(locaux) or 'aucun'})."
    )

    # Tâche 19 : le paramètre sysctl posé par le module de collection doit
    # survivre au reboot (le fichier /etc/sysctl.d/ est réappliqué au boot).
    live = db1.run("sysctl -n vm.swappiness")
    assert live.rc == 0 and live.stdout.strip() == "25", (
        "Après reboot, vm.swappiness n'est plus à 25 : le paramètre a été posé "
        "en runtime sans fichier persistant dans /etc/sysctl.d/.\n"
        f"Vu : {live.stdout.strip()!r}"
    )
