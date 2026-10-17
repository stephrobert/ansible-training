"""Tests pytest+testinfra pour le challenge module copy.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "web1.lab"

BANNER = "/etc/ssh/banner-rhce"
MOTD = "/etc/motd-rhce"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Banner SSH (copy depuis fichier local) ===

def test_banner_ssh_exists(host):
    assert host.file(BANNER).exists, message(
        en=f"{BANNER} is missing. This is the src: half of the challenge: "
           f"ansible.builtin.copy reading challenge/files/banner-ssh.txt, a "
           f"file you create on the control node.",
        fr=f"{BANNER} est absent. C'est la moitié src: du challenge : "
           f"ansible.builtin.copy qui lit challenge/files/banner-ssh.txt, un "
           f"fichier que tu crées sur le control node.",
    )


def test_banner_ssh_mode(host):
    f = host.file(BANNER)
    assert f.mode == 0o644, message(
        en=f"{BANNER} is {oct(f.mode)}, expected 0644. Set mode: \"0644\" in "
           f"quotes, otherwise YAML reads 644 as decimal.",
        fr=f"{BANNER} est en {oct(f.mode)}, attendu 0644. Pose mode: \"0644\" "
           f"entre guillemets, sinon YAML lit 644 en décimal.",
    )
    assert f.user == "root", message(
        en=f"{BANNER} belongs to {f.user}, expected root. Add owner: root, and "
           f"check the play runs with become: true.",
        fr=f"{BANNER} appartient à {f.user}, attendu root. Ajoute owner: root, "
           f"et vérifie que le play tourne avec become: true.",
    )
    assert f.group == "root", message(
        en=f"{BANNER} has group {f.group}, expected root. owner: does not set "
           f"the group: you also need group: root.",
        fr=f"{BANNER} a le groupe {f.group}, attendu root. owner: ne pose pas "
           f"le groupe : il faut aussi group: root.",
    )


def test_banner_ssh_content(host):
    content = host.file(BANNER).content_string
    assert content.startswith("====="), message(
        en="The banner does not start with the ===== line. Copy the mission's "
           "text into challenge/files/banner-ssh.txt exactly, frame included.",
        fr="Le banner ne commence pas par la ligne =====. Recopie le texte de "
           "la mission dans challenge/files/banner-ssh.txt tel quel, cadre "
           "compris.",
    )
    assert "Acces autorise uniquement" in content, message(
        en="The banner does not carry the expected line. The text is given in "
           "the mission, without accents: copy it as it is written there.",
        fr="Le banner ne porte pas la ligne attendue. Le texte est donné dans "
           "la mission, sans accents : recopie-le tel qu'il y figure.",
    )


# === Motd (copy depuis content inline) ===

def test_motd_rhce_exists(host):
    assert host.file(MOTD).exists, message(
        en=f"{MOTD} is missing. This is the content: half: the same module, "
           f"with the text written inline instead of a source file.",
        fr=f"{MOTD} est absent. C'est la moitié content: : le même module, "
           f"avec le texte écrit en ligne au lieu d'un fichier source.",
    )


def test_motd_rhce_mode(host):
    f = host.file(MOTD)
    assert f.mode == 0o644, message(
        en=f"{MOTD} is {oct(f.mode)}, expected 0644. content: takes mode: just "
           f"like src: does.",
        fr=f"{MOTD} est en {oct(f.mode)}, attendu 0644. content: accepte mode: "
           f"exactement comme src:.",
    )


def test_motd_rhce_content(host):
    content = host.file(MOTD).content_string
    assert "Serveur RHCE" in content, message(
        en=f"{MOTD} does not carry « Serveur RHCE ». With content:, a YAML "
           f"block scalar (|) keeps the line breaks.",
        fr=f"{MOTD} ne porte pas « Serveur RHCE ». Avec content:, un bloc YAML "
           f"(|) conserve les retours à la ligne.",
    )
    assert "gere par Ansible" in content, message(
        en=f"{MOTD} does not carry « gere par Ansible ». The text is given in "
           f"the mission, without accents.",
        fr=f"{MOTD} ne porte pas « gere par Ansible ». Le texte est donné dans "
           f"la mission, sans accents.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
