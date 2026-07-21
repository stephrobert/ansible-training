"""Tests pytest+testinfra pour le challenge module uri."""

import json

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"

# Hôte qui sert l'API REST interne du lab, montée par setup.yaml.
# Déclaré dans lab.yaml sous runtime.targets[].roles.api.
API_HOST = "web2.lab"

# Journal d'accès de l'API interne, remis à zéro par setup.yaml.
JOURNAL_API = "/var/log/nginx/lab-uri-api.log"

# Charge utile que sert l'endpoint de référence. Déterministe : l'API est
# servie par le lab, pas par un tiers. On peut donc l'attendre au caractère
# près, là où httpbin n'autorisait qu'un vague « la clé slideshow est là ».
CHARGE_REFERENCE = {
    "api": "inventaire",
    "version": "2026.1",
    "environnements": ["dev", "preprod", "prod"],
    "noeuds_declares": 3,
}

# Corps que le challenge demande d'envoyer en POST.
CORPS_ATTENDU = {"name": "rhce", "version": 2026}


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def api():
    return lab_host(API_HOST)


@pytest.fixture(scope="module")
def journal(api):
    """Entrées du journal d'accès de l'API, une par appel HTTP reçu.

    C'est la PREUVE qu'un appel a réellement eu lieu. Les tests de ce lab ne
    vérifiaient que les fichiers produits sur db1 : un `copy:` au bon contenu,
    écrit à la main, les faisait tous passer sans qu'aucune requête HTTP ne
    parte, alors que le README interdit `command: curl`. Servir l'API depuis
    le lab donne enfin de quoi le vérifier.

    nginx journalise avec `escape=json` : chaque ligne est un objet JSON.
    """
    contenu = api.file(JOURNAL_API).content_string
    entrees = []
    for ligne in contenu.splitlines():
        ligne = ligne.strip()
        if ligne:
            entrees.append(json.loads(ligne))
    return entrees


# === GET ===

def test_get_json_file_exists(host):
    f = host.file("/opt/lab-uri-get.json")
    assert f.exists
    assert f.is_file
    assert f.mode == 0o644


def test_get_json_is_valid_json(host):
    """Le fichier doit porter la charge utile servie par l'API, à l'identique."""
    content = host.file("/opt/lab-uri-get.json").content_string
    data = json.loads(content)
    assert data == CHARGE_REFERENCE, (
        f"Le corps de la réponse GET doit être écrit tel quel. "
        f"Attendu {CHARGE_REFERENCE}, vu {data}"
    )


# === POST ===

def test_post_json_file_exists(host):
    f = host.file("/opt/lab-uri-post.json")
    assert f.exists
    assert f.mode == 0o644


def test_post_response_is_creation_receipt(host):
    """L'API répond 201 avec un accusé de création : c'est lui qu'on persiste."""
    content = host.file("/opt/lab-uri-post.json").content_string
    data = json.loads(content)
    assert data == {"statut": "cree", "ressource": "/api/noeuds/rhce"}, (
        f"La réponse POST analysée doit être écrite telle quelle, vu : {data}"
    )


# === Preuve de l'appel HTTP, côté serveur ===

def test_le_get_a_bien_ete_emis(journal):
    """Un GET a atteint l'endpoint de référence, et il venait du module uri.

    `ansible.builtin.uri` s'annonce `ansible-httpget` (option `http_agent`).
    Un `command: curl`, que le README interdit, s'annoncerait autrement.
    """
    gets = [e for e in journal if e["methode"] == "GET" and e["chemin"] == "/api/reference"]
    assert gets, (
        "Aucun GET sur /api/reference dans le journal de l'API : le fichier "
        f"a-t-il été produit sans appel HTTP ? Journal : {journal}"
    )
    assert any(e["statut"] == "200" for e in gets), f"Aucun GET en 200, vu : {gets}"
    assert any(e["agent"].startswith("ansible-httpget") for e in gets), (
        f"Le GET n'a pas été émis par le module uri (agent vu : "
        f"{[e['agent'] for e in gets]}). Le module s'annonce ansible-httpget."
    )


def test_le_post_a_bien_ete_emis_avec_le_bon_corps(journal):
    """Un POST a déclaré le nœud, avec le corps JSON demandé, et a reçu un 201.

    L'API répond 201 (Created) et non 200 : `status_code: [200, 201]` est donc
    une vraie exigence, que le défaut du module ([200]) ne satisfait pas.
    """
    posts = [e for e in journal if e["methode"] == "POST" and e["chemin"] == "/api/noeuds"]
    assert posts, (
        f"Aucun POST sur /api/noeuds dans le journal de l'API. Journal : {journal}"
    )
    assert any(e["statut"] == "201" for e in posts), (
        f"Le POST n'a pas été accepté en 201, vu : {[e['statut'] for e in posts]}"
    )
    assert any(e["agent"].startswith("ansible-httpget") for e in posts), (
        f"Le POST n'a pas été émis par le module uri (agent vu : "
        f"{[e['agent'] for e in posts]})."
    )
    corps = [json.loads(e["corps"]) for e in posts if e["corps"]]
    assert CORPS_ATTENDU in corps, (
        f"Aucun POST avec le corps {CORPS_ATTENDU}. Corps vus : {corps}. "
        "Le body doit être construit comme une structure YAML, avec "
        "body_format: json."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
