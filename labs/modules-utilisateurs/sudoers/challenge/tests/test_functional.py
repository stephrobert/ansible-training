"""Tests pytest+testinfra pour le challenge module sudoers.

Chaque assertion porte un message, et dans les deux langues : c'est le seul
texte que `dsoxlab check` affiche quand un test échoue. Le fichier ne pouvant
pas exister en deux versions, son nom étant imposé par le contrat, il suit le
modèle de `hints.yaml` et porte ses deux langues avec `message(en=, fr=)`.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"

DEPLOY_SH = "/opt/myapp/bin/deploy.sh"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


@pytest.mark.parametrize("name", [
    "lab-rhce-alice",
    "lab-rhce-ops-team",
    "lab-rhce-alice-as-deploy",
])
def test_sudoers_file_exists_with_perms(host, name):
    f = host.file(f"/etc/sudoers.d/{name}")
    assert f.exists, message(
        en=f"/etc/sudoers.d/{name} is missing. The three rules are three "
           f"community.general.sudoers tasks; the module's name: option is "
           f"what names the file.",
        fr=f"/etc/sudoers.d/{name} est absent. Les trois règles sont trois "
           f"tâches community.general.sudoers ; c'est l'option name: du module "
           f"qui nomme le fichier.",
    )
    assert f.mode == 0o440, message(
        en=f"/etc/sudoers.d/{name} is {oct(f.mode)}, expected 0440. sudo "
           f"IGNORES any file in sudoers.d that is group- or world-writable, "
           f"and says nothing about it: the rule exists and has no effect.",
        fr=f"/etc/sudoers.d/{name} est en {oct(f.mode)}, attendu 0440. sudo "
           f"IGNORE tout fichier de sudoers.d modifiable par le groupe ou les "
           f"autres, et ne le dit pas : la règle existe et ne sert à rien.",
    )
    assert f.user == "root", message(
        en=f"/etc/sudoers.d/{name} belongs to {f.user}, expected root. sudo "
           f"ignores a rule file it does not trust.",
        fr=f"/etc/sudoers.d/{name} appartient à {f.user}, attendu root. sudo "
           f"ignore un fichier de règles auquel il ne fait pas confiance.",
    )


def test_alice_full_sudo(host):
    content = host.file("/etc/sudoers.d/lab-rhce-alice").content_string
    assert content.startswith("alice ALL="), message(
        en=f"The rule does not start with « alice ALL= » (seen: "
           f"'{content.splitlines()[0] if content else ''}'). user: alice with "
           f"commands: ALL is what produces that line.",
        fr=f"La règle ne commence pas par « alice ALL= » (vu : "
           f"'{content.splitlines()[0] if content else ''}'). C'est user: "
           f"alice avec commands: ALL qui produit cette ligne.",
    )
    assert "ALL" in content, message(
        en="alice's rule does not grant ALL. Her rule is the broad one: every "
           "command, but with a password.",
        fr="La règle d'alice n'accorde pas ALL. Sa règle est la large : toutes "
           "les commandes, mais avec mot de passe.",
    )
    assert "NOPASSWD" not in content, message(
        en="alice's rule carries NOPASSWD, which the mission does not ask for. "
           "That is nopassword: false, the module's default, and it is the "
           "whole difference with the ops-team rule.",
        fr="La règle d'alice porte NOPASSWD, que la mission ne demande pas. "
           "C'est nopassword: false, le défaut du module, et c'est toute la "
           "différence avec la règle d'ops-team.",
    )


def test_ops_team_nopasswd(host):
    content = host.file("/etc/sudoers.d/lab-rhce-ops-team").content_string
    assert content.startswith("%ops-team ALL="), message(
        en="The rule does not start with « %ops-team ALL= ». The percent sign "
           "marks a GROUP: the module writes it when you use group: instead "
           "of user:.",
        fr="La règle ne commence pas par « %ops-team ALL= ». Le signe pour "
           "cent marque un GROUPE : le module l'écrit quand on utilise group: "
           "au lieu de user:.",
    )
    assert "NOPASSWD" in content, message(
        en="ops-team's rule does not carry NOPASSWD. That is "
           "nopassword: true, and it is what distinguishes this rule from "
           "alice's.",
        fr="La règle d'ops-team ne porte pas NOPASSWD. C'est nopassword: true, "
           "et c'est ce qui distingue cette règle de celle d'alice.",
    )


def test_bob_member_of_ops_team(host):
    """Prérequis de l'énoncé : bob doit appartenir au groupe ops-team.

    La règle sudo `%ops-team NOPASSWD` ne profite à bob que s'il est
    effectivement membre du groupe (`groups: ops-team, append: true`).
    Sans cette appartenance, la règle de groupe est provisionnée mais
    inopérante pour lui.
    """
    assert host.group("ops-team").exists, message(
        en="The ops-team group does not exist. It comes before the sudo rule: "
           "a rule on a group nobody belongs to grants nothing.",
        fr="Le groupe ops-team n'existe pas. Il vient avant la règle sudo : "
           "une règle sur un groupe sans membre n'accorde rien.",
    )
    assert "ops-team" in host.user("bob").groups, message(
        en="bob is not a member of ops-team, so the %ops-team rule does "
           "nothing for him. Use groups: ops-team with append: true, "
           "otherwise his other groups are replaced.",
        fr="bob n'est pas membre d'ops-team, donc la règle %ops-team ne lui "
           "sert à rien. Utilise groups: ops-team avec append: true, faute de "
           "quoi ses autres groupes sont remplacés.",
    )


def test_alice_runas_deploy(host):
    content = host.file("/etc/sudoers.d/lab-rhce-alice-as-deploy").content_string
    assert "alice ALL=(deploy)" in content, message(
        en="The rule does not carry « alice ALL=(deploy) ». The identity "
           "between parentheses is the runas: option, which says WHO the "
           "command runs as. Without it, sudo falls back to root.",
        fr="La règle ne porte pas « alice ALL=(deploy) ». L'identité entre "
           "parenthèses est l'option runas:, qui dit EN TANT QUE QUI la "
           "commande tourne. Sans elle, sudo retombe sur root.",
    )
    assert "NOPASSWD" in content, message(
        en="This third rule does not carry NOPASSWD, which the mission asks "
           "for: a deployment script is run without a prompt.",
        fr="Cette troisième règle ne porte pas NOPASSWD, que la mission "
           "demande : un script de déploiement se lance sans invite.",
    )
    assert DEPLOY_SH in content, message(
        en=f"The rule does not restrict to {DEPLOY_SH}. Here commands: takes "
           f"that one path and not ALL: this is the narrow rule, and that is "
           f"its point.",
        fr=f"La règle ne restreint pas à {DEPLOY_SH}. Ici commands: prend ce "
           f"seul chemin et non ALL : c'est la règle étroite, et c'est tout "
           f"son intérêt.",
    )


def test_visudo_global_validation(host):
    """visudo -cf doit retourner 0 — pas de regle cassee dans /etc/sudoers."""
    cmd = host.run("sudo visudo -cf /etc/sudoers")
    assert cmd.rc == 0, message(
        en=f"visudo rejects the sudo configuration: {cmd.stderr.strip()}. One "
           f"broken rule in sudoers.d can lock everyone out of sudo, which is "
           f"why the module validates before writing.",
        fr=f"visudo refuse la configuration sudo : {cmd.stderr.strip()}. Une "
           f"seule règle cassée dans sudoers.d peut priver tout le monde de "
           f"sudo, et c'est pour cela que le module valide avant d'écrire.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
