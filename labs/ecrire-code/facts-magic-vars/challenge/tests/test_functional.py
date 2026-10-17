"""Tests pytest+testinfra pour le challenge facts-magic-vars.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import re

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"
SUMMARY_FILE = "/tmp/facts-summary.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_summary_file_exists(host):
    assert host.file(SUMMARY_FILE).exists, message(
        en=f"{SUMMARY_FILE} is missing. The summary gathers facts and magic "
           f"variables in a single file, written with copy and content:.",
        fr=f"{SUMMARY_FILE} est absent. Le résumé rassemble facts et "
           f"variables magiques dans un seul fichier, écrit avec copy et "
           f"content:.",
    )


def test_inventory_hostname_resolved(host):
    content = host.file(SUMMARY_FILE).content_string
    assert "db1_hostname=db1.lab" in content, message(
        en="« db1_hostname=db1.lab » is missing. inventory_hostname is a "
           "MAGIC variable: it is the name the inventory uses, and it needs "
           "no gather_facts.",
        fr="« db1_hostname=db1.lab » manque. inventory_hostname est une "
           "variable MAGIQUE : c'est le nom que porte l'inventaire, et elle "
           "n'a besoin d'aucun gather_facts.",
    )


def test_os_fact(host):
    content = host.file(SUMMARY_FILE).content_string
    assert "db1_os=AlmaLinux" in content, message(
        en="« db1_os=AlmaLinux » is missing. ansible_distribution is a FACT, "
           "not a magic variable: without gather_facts, it does not exist.",
        fr="« db1_os=AlmaLinux » manque. ansible_distribution est un FACT, et "
           "non une variable magique : sans gather_facts, il n'existe pas.",
    )


def test_memory_fact_is_positive_integer(host):
    """db1_memory doit être le fact ansible_memtotal_mb, un entier > 0.

    La valeur exacte dépend de la RAM de la VM (elle change au
    reprovisionnement), donc on prouve la FORME : `db1_memory=<entier positif>`,
    ce qui échoue si le fact est absent, vide ou non numérique.
    """
    content = host.file(SUMMARY_FILE).content_string
    m = re.search(r"^db1_memory=(\d+)$", content, re.MULTILINE)
    assert m, message(
        en=f"The summary must carry 'db1_memory=<integer>' (the "
           f"ansible_memtotal_mb fact).\nSeen: {content.strip()}",
        fr=f"Le résumé doit contenir 'db1_memory=<entier>' (le fact "
           f"ansible_memtotal_mb).\nVu : {content.strip()}",
    )
    assert int(m.group(1)) > 0, message(
        en=f"db1_memory must be a strictly positive integer, seen: "
           f"{m.group(1)}",
        fr=f"db1_memory doit être un entier strictement positif, vu : "
           f"{m.group(1)}",
    )


def test_webservers_group_count(host):
    """Le groupe webservers contient 2 hôtes (web1 + web2)."""
    content = host.file(SUMMARY_FILE).content_string
    assert "webservers_count=2" in content, message(
        en="« webservers_count=2 » is missing. groups is a magic variable: "
           "groups['webservers'] | length counts the hosts of a group, even "
           "those the play does not target.",
        fr="« webservers_count=2 » manque. groups est une variable magique : "
           "groups['webservers'] | length compte les hôtes d'un groupe, même "
           "ceux que le play ne vise pas.",
    )


def test_hostvars_web1_ip(host):
    """hostvars['web1.lab'].ansible_default_ipv4.address = l'IP réelle de web1.

    L'IP attendue est LUE sur web1, jamais codée : Terraform les attribue, et
    elles changent à chaque reprovisionnement. Ce test figeait 10.10.20.21,
    héritée des baux statiques de l'ancien provision.sh.
    """
    expected = lab_host("web1.lab").check_output(
        "ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -1"
    ).strip()
    assert expected, message(
        en="Could not read web1.lab's address: the test cannot establish what "
           "it should compare against.",
        fr="Impossible de lire l'adresse de web1.lab : le test ne peut pas "
           "établir ce à quoi il devrait comparer.",
    )
    content = host.file(SUMMARY_FILE).content_string
    assert f"web1_ip={expected}" in content, message(
        en=f"hostvars['web1.lab'].ansible_default_ipv4.address must return "
           f"web1's IP ({expected}).\nSeen in the summary: "
           f"{content.strip()}\nAn empty value means facts were never "
           f"gathered on web1: hostvars only carries what has been collected.",
        fr=f"L'accès via hostvars['web1.lab'].ansible_default_ipv4.address "
           f"doit retourner l'IP de web1 ({expected}).\nVu dans le résumé : "
           f"{content.strip()}\nSi la valeur est vide, les facts n'ont jamais "
           f"été collectés sur web1 : hostvars ne porte que ce qui a été "
           f"ramassé.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
