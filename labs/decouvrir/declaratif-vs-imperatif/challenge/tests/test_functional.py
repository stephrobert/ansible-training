"""Challenge « déclaratif vs impératif » — convertir un script Bash en playbook.

Objectif EX294 : réécrire le script impératif
`scripts/install-nginx-impératif.sh` en un playbook Ansible **déclaratif et
idempotent** produisant le MÊME état système sur `web1.lab`.

Ces tests prouvent l'ÉTAT du système (paquet, service, pare-feu, contenu de
la page), pas qu'une commande a tourné, puis vérifient l'idempotence stricte
(changed=0 au second passage) — le critère du RHCE.

La solution évaluée est résolue par le conftest :
  - `challenge/solution.yml` (votre travail) s'il existe,
  - sinon `solution/decouvrir/declaratif-vs-imperatif/solution.yml` (référence
    chiffrée du formateur).

Lancement depuis la racine du repo :
    pytest -v labs/decouvrir/declaratif-vs-imperatif/challenge/tests/
"""

import pytest

from conftest import lab_host, assert_idempotent

TARGET_HOST = "web1.lab"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


def test_nginx_installed(host):
    """Le paquet nginx doit être installé (état, pas trace d'une commande dnf)."""
    assert host.package("nginx").is_installed, (
        "nginx n'est pas installé sur web1.lab. La tâche déclarative attendue : "
        "ansible.builtin.dnf avec state: present."
    )


def test_nginx_enabled_and_running(host):
    """Le service doit être actif ET activé au boot (persistance du service)."""
    nginx = host.service("nginx")
    assert nginx.is_running, "Le service nginx n'est pas démarré (state: started)."
    assert nginx.is_enabled, (
        "Le service nginx n'est pas activé au boot (enabled: true) : il ne "
        "redémarrerait pas après reboot."
    )


def test_firewalld_http_open_runtime(host):
    """Le service http doit être ouvert dans la zone active (effet immédiat)."""
    services = host.run("firewall-cmd --list-services").stdout
    assert "http" in services.split(), (
        f"http n'est pas ouvert dans firewalld (runtime). Services vus : {services!r}. "
        "La tâche attendue : ansible.posix.firewalld service=http state=enabled immediate=true."
    )


def test_firewalld_http_open_permanent(host):
    """http doit aussi être ouvert de façon PERMANENTE : sinon perdu au reload/reboot.

    C'est le piège classique du pare-feu : une règle runtime seule disparaît au
    prochain `firewall-cmd --reload`. On exige donc `permanent: true`, prouvé
    ici sans redémarrer la VM.
    """
    services = host.run("firewall-cmd --permanent --list-services").stdout
    assert "http" in services.split(), (
        f"http n'est pas ouvert de façon PERMANENTE. Permanent : {services!r}. "
        "Ajoutez permanent: true à la tâche firewalld."
    )


def test_index_contains_exactly_one_servi_par_line(host):
    """Le cœur du lab : UNE SEULE ligne « Servi par ... », quel que soit le nombre de runs.

    Le script Bash faisait un `tee -a` (append) : il ajoutait une ligne à
    chaque exécution et dérivait. Un playbook déclaratif idempotent (lineinfile
    avec regexp, ou copy/template) converge vers exactement une occurrence.
    """
    page = host.file("/usr/share/nginx/html/index.html").content_string
    occurrences = page.count("Servi par")
    assert occurrences == 1, (
        f"index.html doit contenir EXACTEMENT 1 ligne « Servi par » "
        f"(preuve d'idempotence de l'état), trouvé : {occurrences}. "
        f"Un append non idempotent (echo >> / tee -a) en accumulerait une par run."
    )


def test_servi_par_line_is_a_paragraph(host):
    """La ligne produite doit être le paragraphe HTML attendu, pas un texte brut.

    On ne vérifie pas le hostname exact (web1 vs web1.lab) : c'est un détail de
    forme. On vérifie que l'état visé est bien une balise <p>Servi par ...</p>,
    comme le produit le script de référence.
    """
    page = host.file("/usr/share/nginx/html/index.html").content_string
    servi = [line for line in page.splitlines() if "Servi par" in line]
    assert servi, "Aucune ligne « Servi par » dans index.html."
    line = servi[0].strip()
    assert line.startswith("<p>Servi par ") and line.endswith("</p>"), (
        f"La ligne attendue est un paragraphe <p>Servi par ...</p>, vu : {line!r}."
    )


def test_page_served_over_http(host):
    """nginx sert bien la page personnalisée : preuve bout-en-bout que le service tourne."""
    served = host.run("curl -s http://localhost/").stdout
    assert "Servi par" in served, (
        "La page servie par nginx ne contient pas « Servi par » : le service "
        "sert-il bien /usr/share/nginx/html/index.html ?"
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    C'est ce qui distingue un vrai playbook déclaratif d'un script Bash traduit
    en YAML. `assert_idempotent` rejoue la solution en jeu (celle de l'apprenant
    si elle existe, sinon la référence) et exige changed=0 partout.
    """
    assert_idempotent(__file__)
