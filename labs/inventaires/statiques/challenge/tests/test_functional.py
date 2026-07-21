"""Tests pytest pour le lab « écrire un inventaire statique de zéro ».

Le LIVRABLE de ce lab est un inventaire, pas un playbook. L'apprenant écrit
`inventory/hosts.yml` ; le formateur fournit la référence chiffrée sous
`solution/inventaires/statiques/inventory/`. Le conftest résout l'un ou l'autre
via `lab_inventory_args()` (travail de l'apprenant s'il existe, référence
chiffrée sinon).

Principe de preuve : aucune assertion ne lit le TEXTE du fichier. Un fichier
est forgeable et ne prouve rien. Tout passe par :

  1. la résolution d'Ansible lui-même (`ansible-inventory --list` / `--host`) :
     ce qu'Ansible VOIT réellement, groupes, enfants et variables héritées ;
  2. une connexion réelle (`ansible <groupe> -m ping`) : le pattern joint
     EXACTEMENT les bons hôtes, et ils répondent vraiment.

Un inventaire syntaxiquement plausible mais faux (un hôte oublié d'un groupe,
un parent qui n'agrège pas ses enfants) échoue à la fois sur le graphe résolu
et sur le compte de « pong ».
"""

import json
import subprocess

import pytest

from conftest import REPO_ROOT, lab_inventory_args

# Ce module n'a pas de playbook à rejouer (son livrable est l'inventaire). Sans
# ce marqueur, la fixture de replay du conftest skipperait le module, faute de
# solution.yml. Le poser via os.environ["LAB_NO_REPLAY"] le désactiverait pour
# TOUTE la session, y compris les labs voisins : le marqueur le limite à ce
# module.
pytestmark = pytest.mark.no_replay


def _inventory_list():
    """Inventaire RÉSOLU par Ansible, au format JSON (`ansible-inventory --list`)."""
    res = subprocess.run(
        ["ansible-inventory", *lab_inventory_args(__file__), "--list"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        "ansible-inventory n'a pas su lire l'inventaire du lab :\n"
        f"--- stderr ---\n{res.stderr.strip()}"
    )
    return json.loads(res.stdout)


def _inventory_host(host):
    """Variables RÉSOLUES d'un hôte (`ansible-inventory --host`), group_vars fusionnées."""
    res = subprocess.run(
        ["ansible-inventory", *lab_inventory_args(__file__), "--host", host],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"ansible-inventory --host {host} a échoué :\n"
        f"--- stderr ---\n{res.stderr.strip()}"
    )
    return json.loads(res.stdout)


def _ping(pattern):
    """Lance `ansible <pattern> -m ping` à travers l'inventaire du lab."""
    return subprocess.run(
        ["ansible", *lab_inventory_args(__file__), pattern,
         "-m", "ansible.builtin.ping"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _pongs(res):
    """Nombre de « pong » dans la sortie d'un run ansible ping."""
    return res.stdout.count('"ping": "pong"')


# ─── Structure : les groupes déclarent les bons hôtes ─────────────────────
def test_les_groupes_declarent_les_bons_hotes():
    """webservers = {web1, web2}, dbservers = {db1}, tels qu'Ansible les résout.

    On lit l'inventaire RÉSOLU (`--list`), pas le texte du fichier : un groupe
    absent, ou dont un hôte manque, se voit ici quelle que soit la façon dont
    le fichier est écrit (INI, YAML, une ou plusieurs sources).
    """
    inv = _inventory_list()

    assert "webservers" in inv, (
        f"Groupe `webservers` absent de l'inventaire résolu. Groupes vus : "
        f"{sorted(g for g in inv if g != '_meta')}"
    )
    assert sorted(inv["webservers"].get("hosts", [])) == ["web1.lab", "web2.lab"], (
        "Le groupe `webservers` doit contenir EXACTEMENT web1.lab et web2.lab, "
        f"vu : {sorted(inv['webservers'].get('hosts', [])) or 'aucun hôte'}."
    )

    assert "dbservers" in inv, (
        f"Groupe `dbservers` absent de l'inventaire résolu. Groupes vus : "
        f"{sorted(g for g in inv if g != '_meta')}"
    )
    assert sorted(inv["dbservers"].get("hosts", [])) == ["db1.lab"], (
        "Le groupe `dbservers` doit contenir EXACTEMENT db1.lab, "
        f"vu : {sorted(inv['dbservers'].get('hosts', [])) or 'aucun hôte'}."
    )


# ─── Structure : le groupe parent agrège ses enfants ──────────────────────
def test_le_groupe_parent_agrege_ses_enfants():
    """Le groupe `datacenter` doit référencer webservers ET dbservers comme enfants.

    C'est la notion de `children` : un groupe qui n'a pas d'hôte en propre mais
    regroupe d'autres groupes. On le lit dans l'inventaire résolu, pas dans le
    fichier.
    """
    inv = _inventory_list()

    assert "datacenter" in inv, (
        f"Groupe parent `datacenter` absent de l'inventaire résolu. Groupes "
        f"vus : {sorted(g for g in inv if g != '_meta')}"
    )
    enfants = set(inv["datacenter"].get("children", []))
    assert {"webservers", "dbservers"} <= enfants, (
        "Le groupe parent `datacenter` doit agréger webservers ET dbservers "
        f"via `children`, enfants vus : {sorted(enfants) or 'aucun'}.\n"
        "Un parent qui ne référence pas ses deux enfants ne joindra pas tous "
        "les hôtes du site."
    )


# ─── Connexion réelle : chaque groupe joint EXACTEMENT ses hôtes ──────────
def test_le_ping_par_groupe_joint_exactement_les_bons_hotes():
    """Preuve par connexion : le pattern touche les bons hôtes, et eux seuls.

    C'est le test le plus difficile à tromper : un « pong » ne s'obtient qu'en
    joignant réellement l'hôte à travers l'inventaire (bon groupe, bon hôte,
    bon utilisateur `student`, bon ssh_config). Un fichier plausible mais faux
    ne produit pas le bon compte de « pong ».
    """
    web = _ping("webservers")
    assert web.returncode == 0, (
        "Le ping du groupe `webservers` a échoué :\n"
        f"--- stdout ---\n{web.stdout.strip()}\n"
        f"--- stderr ---\n{web.stderr.strip()}"
    )
    assert "web1.lab | SUCCESS" in web.stdout and "web2.lab | SUCCESS" in web.stdout, (
        "web1.lab et web2.lab doivent répondre au ping via `webservers`.\n"
        f"Vu :\n{web.stdout.strip()}"
    )
    assert "db1.lab" not in web.stdout, (
        "db1.lab NE doit PAS être joint par le groupe `webservers` : il n'y a "
        f"pas sa place.\nVu :\n{web.stdout.strip()}"
    )
    assert _pongs(web) == 2, (
        f"Exactement 2 « pong » attendus pour `webservers`, vu {_pongs(web)}.\n"
        f"{web.stdout.strip()}"
    )

    db = _ping("dbservers")
    assert db.returncode == 0, (
        f"Le ping du groupe `dbservers` a échoué :\n{db.stdout.strip()}\n"
        f"{db.stderr.strip()}"
    )
    assert "db1.lab | SUCCESS" in db.stdout and _pongs(db) == 1, (
        "Seul db1.lab doit répondre via `dbservers` (1 « pong » attendu), vu "
        f"{_pongs(db)}.\n{db.stdout.strip()}"
    )
    assert "web1.lab" not in db.stdout and "web2.lab" not in db.stdout, (
        "Aucun webserver ne doit être joint par `dbservers`.\n"
        f"Vu :\n{db.stdout.strip()}"
    )

    dc = _ping("datacenter")
    assert dc.returncode == 0, (
        f"Le ping du groupe parent `datacenter` a échoué :\n{dc.stdout.strip()}\n"
        f"{dc.stderr.strip()}"
    )
    assert _pongs(dc) == 3, (
        "Le groupe parent `datacenter` doit joindre les 3 hôtes de ses groupes "
        f"enfants (3 « pong » attendus), vu {_pongs(dc)}.\n"
        "Un parent qui n'agrège pas correctement ses enfants en joint moins.\n"
        f"{dc.stdout.strip()}"
    )
    for hote in ("web1.lab", "web2.lab", "db1.lab"):
        assert f"{hote} | SUCCESS" in dc.stdout, (
            f"{hote} doit être joint via le groupe parent `datacenter`.\n"
            f"Vu :\n{dc.stdout.strip()}"
        )


# ─── Variables de groupe : résolues et cloisonnées par Ansible ────────────
def test_les_variables_de_groupe_sont_resolues_et_cloisonnees():
    """Les group_vars sont résolues par Ansible, chacune dans sa portée.

    On interroge les variables EFFECTIVES d'un hôte (`--host`), c'est-à-dire ce
    qu'un playbook verrait après fusion. Deux preuves en une :

    - `web_role` (défini sur webservers) atteint web1 mais PAS db1 : la portée
      d'une variable de groupe est bien le groupe ;
    - `site` (défini sur le parent datacenter) est hérité par web1 ET db1 : un
      hôte hérite des variables des groupes parents de ses groupes.

    Recopier ces valeurs en dur host par host donnerait le même résultat visuel
    mais raterait la démonstration : l'objectif est de les porter par le GROUPE.
    """
    web1 = _inventory_host("web1.lab")
    assert web1.get("web_role") == "frontend", (
        "La variable de groupe `web_role` (portée par webservers) doit être "
        f"résolue sur web1.lab avec la valeur « frontend », vu : "
        f"{web1.get('web_role')!r}."
    )
    assert web1.get("site") == "paris", (
        "web1.lab doit hériter de `site` (portée par le parent datacenter), vu : "
        f"{web1.get('site')!r}."
    )
    assert "db_role" not in web1, (
        "`db_role` est une variable du groupe dbservers : elle ne doit PAS "
        f"fuiter sur web1.lab (vu : {web1.get('db_role')!r})."
    )

    db1 = _inventory_host("db1.lab")
    assert db1.get("db_role") == "database", (
        "La variable de groupe `db_role` (portée par dbservers) doit être "
        f"résolue sur db1.lab avec la valeur « database », vu : "
        f"{db1.get('db_role')!r}."
    )
    assert db1.get("site") == "paris", (
        "db1.lab doit hériter de `site` via le parent datacenter, vu : "
        f"{db1.get('site')!r}. Si l'héritage manque, le parent n'agrège pas "
        "réellement ses enfants."
    )
    assert "web_role" not in db1, (
        "`web_role` est une variable du groupe webservers : elle ne doit PAS "
        f"fuiter sur db1.lab (vu : {db1.get('web_role')!r})."
    )
