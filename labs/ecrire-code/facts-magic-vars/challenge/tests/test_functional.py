"""Tests pytest+testinfra pour le challenge facts-magic-vars."""

import re

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "db1.lab"
SUMMARY_FILE = "/tmp/facts-summary.txt"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_summary_file_exists(host):
    assert host.file(SUMMARY_FILE).exists


def test_inventory_hostname_resolved(host):
    content = host.file(SUMMARY_FILE).content_string
    assert "db1_hostname=db1.lab" in content


def test_os_fact(host):
    content = host.file(SUMMARY_FILE).content_string
    assert "db1_os=AlmaLinux" in content


def test_memory_fact_is_positive_integer(host):
    """db1_memory doit être le fact ansible_memtotal_mb, un entier > 0.

    La valeur exacte dépend de la RAM de la VM (elle change au
    reprovisionnement), donc on prouve la FORME : `db1_memory=<entier positif>`,
    ce qui échoue si le fact est absent, vide ou non numérique.
    """
    content = host.file(SUMMARY_FILE).content_string
    m = re.search(r"^db1_memory=(\d+)$", content, re.MULTILINE)
    assert m, (
        "Le résumé doit contenir 'db1_memory=<entier>' (fact "
        f"ansible_memtotal_mb).\nVu : {content.strip()}"
    )
    assert int(m.group(1)) > 0, (
        f"db1_memory doit être un entier strictement positif, vu : {m.group(1)}"
    )


def test_webservers_group_count(host):
    """Le groupe webservers contient 2 hôtes (web1 + web2)."""
    content = host.file(SUMMARY_FILE).content_string
    assert "webservers_count=2" in content


def test_hostvars_web1_ip(host):
    """hostvars['web1.lab'].ansible_default_ipv4.address = l'IP réelle de web1.

    L'IP attendue est LUE sur web1, jamais codée : Terraform les attribue, et
    elles changent à chaque reprovisionnement. Ce test figeait 10.10.20.21,
    héritée des baux statiques de l'ancien provision.sh.
    """
    expected = lab_host("web1.lab").check_output(
        "ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -1"
    ).strip()
    assert expected, "Impossible de lire l'adresse de web1.lab."
    content = host.file(SUMMARY_FILE).content_string
    assert f"web1_ip={expected}" in content, (
        "L'accès via hostvars['web1.lab'].ansible_default_ipv4.address doit "
        f"retourner l'IP de web1 ({expected}).\n"
        f"Vu dans le résumé : {content.strip()}\n"
        "Si la valeur est vide, le pre-gather sur web1 n'a pas tourné."
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
