"""Tests pytest+testinfra pour le challenge module get_url.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import json

import pytest

from conftest import assert_idempotent, lab_host, message

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
    assert f.exists, message(
        en=f"{path} was not downloaded. Use ansible.builtin.get_url with the "
           f"depot URL: command: curl and command: wget are forbidden here, "
           f"and the access log would catch them.",
        fr=f"{path} n'a pas été téléchargé. Utilise ansible.builtin.get_url "
           f"avec l'URL du dépôt : command: curl et command: wget sont "
           f"interdits ici, et le journal d'accès les démasquerait.",
    )
    assert f.is_file, message(
        en=f"{path} exists but is not an ordinary file. A dest: ending with a "
           f"slash makes get_url write INSIDE a directory.",
        fr=f"{path} existe mais n'est pas un fichier ordinaire. Un dest: qui "
           f"finit par une barre oblique fait écrire get_url DANS un "
           f"répertoire.",
    )
    assert f.mode == 0o644, message(
        en=f"{path} is {oct(f.mode)}, expected 0644. get_url takes mode: like "
           f"copy does.",
        fr=f"{path} est en {oct(f.mode)}, attendu 0644. get_url accepte mode: "
           f"comme copy.",
    )


def test_gpl3_content(host):
    """Verifier que le contenu correspond au texte GPL v3."""
    content = host.file("/opt/lab-gpl3.txt").content_string
    assert "GNU GENERAL PUBLIC LICENSE" in content, message(
        en="/opt/lab-gpl3.txt does not hold the GPL text. Check the URL: the "
           "public area serves /depot/gpl-3.0.txt.",
        fr="/opt/lab-gpl3.txt ne porte pas le texte de la GPL. Vérifie l'URL : "
           "la zone publique sert /depot/gpl-3.0.txt.",
    )
    assert "Version 3" in content, message(
        en="The downloaded text is not version 3 of the licence.",
        fr="Le texte téléchargé n'est pas la version 3 de la licence.",
    )
    # Le fichier GPL fait ~35K caracteres
    assert len(content) > 30000, message(
        en=f"/opt/lab-gpl3.txt holds only {len(content)} characters, expected "
           f"about 35000. A file this short is usually an error page saved by "
           f"a download that did not check its status code.",
        fr=f"/opt/lab-gpl3.txt ne porte que {len(content)} caractères, attendu "
           f"environ 35000. Un fichier aussi court est en général une page "
           f"d'erreur enregistrée par un téléchargement qui n'a pas regardé "
           f"son code de retour.",
    )


def test_lgpl3_content(host):
    """Verifier que le contenu correspond au texte LGPL v3."""
    content = host.file("/opt/lab-lgpl3.txt").content_string
    assert "GNU LESSER GENERAL PUBLIC LICENSE" in content, message(
        en="/opt/lab-lgpl3.txt does not hold the LGPL text. This one lives in "
           "the protected area, /prive/lgpl-3.0.txt, and needs url_username "
           "and url_password.",
        fr="/opt/lab-lgpl3.txt ne porte pas le texte de la LGPL. Celui-ci vit "
           "dans la zone protégée, /prive/lgpl-3.0.txt, et demande "
           "url_username et url_password.",
    )
    assert "Version 3" in content, message(
        en="The downloaded text is not version 3 of the lesser licence.",
        fr="Le texte téléchargé n'est pas la version 3 de la licence lesser.",
    )


def test_gpl3_integrite_conforme_au_depot(host, api):
    """Le fichier reçu porte exactement l'empreinte que le dépôt publie.

    Aucune empreinte n'est figée ici : on relit celle que le dépôt sert, et on
    la compare à celle du fichier arrivé sur db1. Le paquet gmp peut changer de
    version, le test reste juste.
    """
    publiee = api.file(SOMMES_PUBLIEES).content_string.split()[0]
    recue = host.file("/opt/lab-gpl3.txt").sha256sum
    assert recue == publiee, message(
        en=f"The downloaded file does not match the checksum the depot "
           f"publishes.\n  published: {publiee}\n  received : {recue}",
        fr=f"Le fichier téléchargé ne correspond pas à l'empreinte publiée par "
           f"le dépôt.\n  publiée : {publiee}\n  reçue   : {recue}",
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
    assert sommes, message(
        en=f"The checksum file was never requested from the depot, so the "
           f"download's integrity is not verified. Use "
           f"checksum: sha256:<url of the .sha256 file>. Log: {journal}",
        fr=f"Le fichier de sommes de contrôle n'a jamais été demandé au dépôt : "
           f"l'intégrité du téléchargement n'est donc pas vérifiée. Utilise "
           f"checksum: sha256:<url du fichier .sha256>. Journal : {journal}",
    )
    assert any(e["statut"] == "200" for e in sommes), message(
        en=f"The checksum file was not served correctly: {sommes}",
        fr=f"Le fichier de sommes n'a pas été servi correctement : {sommes}",
    )
    assert any(e["agent"].startswith("ansible-httpget") for e in sommes), message(
        en=f"The request did not come from get_url (agent seen: "
           f"{[e['agent'] for e in sommes]}). The module announces itself as "
           f"ansible-httpget; curl and wget are forbidden.",
        fr=f"Requête non émise par get_url (agent vu : "
           f"{[e['agent'] for e in sommes]}). Le module s'annonce "
           f"ansible-httpget ; curl et wget sont interdits.",
    )


def test_telechargement_authentifie(journal):
    """La zone protégée a rendu le fichier, donc l'authentification a réussi.

    Sans identifiants, nginx rend 401 et rien n'est écrit (vérifié) : la
    présence du fichier prouve déjà l'authentification. Le journal ajoute la
    preuve que c'est bien get_url qui a fait la requête, et non un curl.
    """
    prives = [e for e in journal if e["chemin"].endswith("/prive/lgpl-3.0.txt")]
    assert prives, message(
        en=f"No request reached the depot's protected area. Log: {journal}",
        fr=f"Aucune requête sur la zone protégée du dépôt. Journal : {journal}",
    )
    assert any(e["statut"] == "200" for e in prives), message(
        en=f"The protected area never returned 200: did authentication "
           f"succeed? Codes seen: {[e['statut'] for e in prives]}",
        fr=f"La zone protégée n'a jamais rendu 200 : l'authentification a-t-elle "
           f"abouti ? Codes vus : {[e['statut'] for e in prives]}",
    )
    assert any(e["agent"].startswith("ansible-httpget") for e in prives), message(
        en=f"The request did not come from get_url (agent seen: "
           f"{[e['agent'] for e in prives]}).",
        fr=f"Requête non émise par get_url (agent vu : "
           f"{[e['agent'] for e in prives]}).",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
