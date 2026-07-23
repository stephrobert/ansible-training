"""Tests pytest+testinfra pour le challenge module get_url."""

import json

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"

# Hôte qui sert le dépôt de référence interne, monté par setup.yaml.
# Déclaré dans lab.yaml sous runtime.targets[].roles.api.
API_HOST = "web2.lab"

# Journal d'accès du dépôt, remis à zéro par setup.yaml.
JOURNAL_DEPOT = "/var/log/nginx/lab-get-url-depot.log"

# Fichier de sommes de contrôle publié par le dépôt, à côté du texte servi.
SOMMES_PUBLIEES = "/var/www/lab-get-url/depot/gpl-3.0.txt.sha256"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.fixture(scope="module")
def api():
    return lab_host(API_HOST)


@pytest.fixture(scope="module")
def journal(api):
    """Entrées du journal d'accès du dépôt, une par requête HTTP reçue.

    C'est la PREUVE que le téléchargement est bien passé par le réseau, et par
    le module. nginx journalise avec `escape=json` : une ligne = un objet JSON.
    """
    contenu = api.file(JOURNAL_DEPOT).content_string
    entrees = []
    for ligne in contenu.splitlines():
        ligne = ligne.strip()
        if ligne:
            entrees.append(json.loads(ligne))
    return entrees


@pytest.mark.parametrize("path", [
    "/opt/lab-gpl3.txt",
    "/opt/lab-lgpl3.txt",
])
def test_files_downloaded(host, path):
    f = host.file(path)
    assert f.exists, f"{path} doit exister"
    assert f.is_file
    assert f.mode == 0o644


def test_gpl3_content(host):
    """Verifier que le contenu correspond au texte GPL v3."""
    content = host.file("/opt/lab-gpl3.txt").content_string
    assert "GNU GENERAL PUBLIC LICENSE" in content
    assert "Version 3" in content
    # Le fichier GPL fait ~35K caracteres
    assert len(content) > 30000


def test_lgpl3_content(host):
    """Verifier que le contenu correspond au texte LGPL v3."""
    content = host.file("/opt/lab-lgpl3.txt").content_string
    assert "GNU LESSER GENERAL PUBLIC LICENSE" in content
    assert "Version 3" in content


def test_gpl3_integrite_conforme_au_depot(host, api):
    """Le fichier reçu porte exactement l'empreinte que le dépôt publie.

    Aucune empreinte n'est figée ici : on relit celle que le dépôt sert, et on
    la compare à celle du fichier arrivé sur db1. Le paquet gmp peut changer de
    version, le test reste juste.
    """
    publiee = api.file(SOMMES_PUBLIEES).content_string.split()[0]
    recue = host.file("/opt/lab-gpl3.txt").sha256sum
    assert recue == publiee, (
        f"Le fichier téléchargé ne correspond pas à l'empreinte publiée par le "
        f"dépôt.\n  publiée : {publiee}\n  reçue   : {recue}"
    )


def test_checksum_reellement_verifie(journal):
    """Le fichier de sommes a été consulté : `checksum:` n'est pas resté sur le papier.

    `checksum: sha256:<url>` fait télécharger le fichier de sommes AVANT le
    fichier lui-même. Sans cette option, get_url ne le demande jamais (vérifié)
    et cette ligne est absente du journal : le test échoue. C'est ce qui rend
    la compétence `checksum` annoncée par lab.yaml réellement éprouvée, au lieu
    d'être une promesse que le challenge mettait « hors scope ».
    """
    sommes = [e for e in journal if e["chemin"].endswith("gpl-3.0.txt.sha256")]
    assert sommes, (
        "Le fichier de sommes de contrôle n'a jamais été demandé au dépôt : "
        "l'intégrité du téléchargement n'est donc pas vérifiée. Utilisez "
        "checksum: sha256:<url du fichier .sha256>. "
        f"Journal : {journal}"
    )
    assert any(e["statut"] == "200" for e in sommes), (
        f"Le fichier de sommes n'a pas été servi correctement : {sommes}"
    )
    assert any(e["agent"].startswith("ansible-httpget") for e in sommes), (
        f"Requête non émise par get_url (agent vu : {[e['agent'] for e in sommes]}). "
        "Le module s'annonce ansible-httpget ; curl et wget sont interdits."
    )


def test_telechargement_authentifie(journal):
    """La zone protégée a rendu le fichier, donc l'authentification a réussi.

    Sans identifiants, nginx rend 401 et rien n'est écrit (vérifié) : la
    présence du fichier prouve déjà l'authentification. Le journal ajoute la
    preuve que c'est bien get_url qui a fait la requête, et non un curl.
    """
    prives = [e for e in journal if e["chemin"].endswith("/prive/lgpl-3.0.txt")]
    assert prives, (
        f"Aucune requête sur la zone protégée du dépôt. Journal : {journal}"
    )
    assert any(e["statut"] == "200" for e in prives), (
        f"La zone protégée n'a jamais rendu 200 : l'authentification a-t-elle "
        f"abouti ? Codes vus : {[e['statut'] for e in prives]}"
    )
    assert any(e["agent"].startswith("ansible-httpget") for e in prives), (
        f"Requête non émise par get_url (agent vu : {[e['agent'] for e in prives]})."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
