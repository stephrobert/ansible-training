"""Tests pytest+testinfra pour le challenge module authorized_key.

Chaque assertion porte un message, et dans les deux langues. Depuis dsoxlab
0.4.0, `dsoxlab check` n'affiche plus le traceback de pytest mais le **nom des
tests en échec et le message écrit ici** : sans message, l'apprenant lit
« alice authorized keys perms » et rien sur ce qu'il doit corriger.

Le fichier ne peut pas exister en deux versions, son nom étant imposé par le
contrat. Il suit donc le modèle de `hints.yaml`, qui porte lui aussi ses deux
langues dans un seul fichier : `message(en=..., fr=...)`, fourni par le
`conftest.py` du dépôt.
"""

import pytest

from conftest import assert_idempotent, lab_host, message

TARGET_HOST = "db1.lab"

RESEAU_AUTORISE = '10.10.20.0/24'
COMMANDE_FORCEE = '/usr/local/bin/backup.sh'


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Permissions strictes ===

def test_alice_authorized_keys_perms(host):
    f = host.file("/home/alice/.ssh/authorized_keys")
    assert f.exists, message(
        en="/home/alice/.ssh/authorized_keys is missing. The module creates it "
           "on its own: ansible.posix.authorized_key with user: alice. If the "
           "user does not exist yet, create it first with ansible.builtin.user.",
        fr="/home/alice/.ssh/authorized_keys est absent. Le module le crée "
           "lui-même : ansible.posix.authorized_key avec user: alice. Si le "
           "compte n'existe pas encore, crée-le d'abord avec ansible.builtin.user.",
    )
    assert f.mode == 0o600, message(
        en=f"/home/alice/.ssh/authorized_keys is {oct(f.mode)}, expected 0600. "
           f"The module sets it; a mode this wrong usually means the file was "
           f"written by hand, with copy or lineinfile, instead.",
        fr=f"/home/alice/.ssh/authorized_keys est en {oct(f.mode)}, attendu 0600. "
           f"Le module le pose lui-même : un mode aussi faux signale en général "
           f"un fichier écrit à la main, avec copy ou lineinfile.",
    )
    assert f.user == "alice", message(
        en=f"/home/alice/.ssh/authorized_keys belongs to {f.user}, expected "
           f"alice. sshd ignores a key file the account does not own.",
        fr=f"/home/alice/.ssh/authorized_keys appartient à {f.user}, attendu "
           f"alice. sshd ignore un fichier de clés que le compte ne possède pas.",
    )


def test_alice_ssh_dir_perms(host):
    d = host.file("/home/alice/.ssh")
    assert d.is_directory, message(
        en="/home/alice/.ssh is not a directory. ansible.posix.authorized_key "
           "creates it with the right mode: let it do so rather than making it "
           "yourself.",
        fr="/home/alice/.ssh n'est pas un répertoire. "
           "ansible.posix.authorized_key le crée avec le bon mode : laisse-le "
           "faire plutôt que de le créer toi-même.",
    )
    assert d.mode == 0o700, message(
        en=f"/home/alice/.ssh is {oct(d.mode)}, expected 0700. sshd refuses to "
           f"read keys from a directory other users can enter.",
        fr=f"/home/alice/.ssh est en {oct(d.mode)}, attendu 0700. sshd refuse de "
           f"lire des clés dans un répertoire où d'autres peuvent entrer.",
    )


def test_bob_authorized_keys_perms(host):
    f = host.file("/home/bob/.ssh/authorized_keys")
    assert f.exists, message(
        en="/home/bob/.ssh/authorized_keys is missing. Same task as for alice, "
           "with user: bob.",
        fr="/home/bob/.ssh/authorized_keys est absent. Même tâche que pour "
           "alice, avec user: bob.",
    )
    assert f.mode == 0o600, message(
        en=f"/home/bob/.ssh/authorized_keys is {oct(f.mode)}, expected 0600.",
        fr=f"/home/bob/.ssh/authorized_keys est en {oct(f.mode)}, attendu 0600.",
    )
    assert f.user == "bob", message(
        en=f"/home/bob/.ssh/authorized_keys belongs to {f.user}, expected bob.",
        fr=f"/home/bob/.ssh/authorized_keys appartient à {f.user}, attendu bob.",
    )


# === Cle libre d alice ===

def test_alice_has_personal_key(host):
    content = host.file("/home/alice/.ssh/authorized_keys").content_string
    assert "alice@laptop" in content, message(
        en="alice's personal key is not deployed. Its comment, alice@laptop, "
           "is what identifies it. Read files/alice.pub.key.pub, the PUBLIC "
           "one despite the name, with lookup('file', ...).",
        fr="La clé personnelle d'alice n'est pas déployée. C'est son "
           "commentaire, alice@laptop, qui l'identifie. Lis "
           "files/alice.pub.key.pub, la PUBLIQUE malgré son nom, avec "
           "lookup('file', ...).",
    )


# === Cle service d alice ===

def test_alice_has_service_key_with_command(host):
    content = host.file("/home/alice/.ssh/authorized_keys").content_string
    assert "backup@service" in content, message(
        en="The backup@service key is missing from alice's account. It is a "
           "third key, in the same file as her personal one: the module adds, "
           "it does not replace, as long as state: present.",
        fr="La clé backup@service manque dans le compte d'alice. C'est une "
           "troisième clé, dans le même fichier que sa clé personnelle : le "
           "module ajoute, il ne remplace pas, tant que state: present.",
    )
    assert f'command="{COMMANDE_FORCEE}"' in content, message(
        en=f"The backup@service key does not force its command. Add "
           f"key_options: 'command=\"{COMMANDE_FORCEE}\"' so that this key can "
           f"only run that script, whatever the client asks for.",
        fr=f"La clé backup@service ne force pas sa commande. Ajoute "
           f"key_options: 'command=\"{COMMANDE_FORCEE}\"' pour que cette clé ne "
           f"puisse lancer que ce script, quoi que demande le client.",
    )
    assert "no-pty" in content, message(
        en="The backup@service key is missing no-pty. Without it, the key can "
           "still open an interactive terminal, which defeats the forced "
           "command. Both options go in the same key_options.",
        fr="Il manque no-pty à la clé backup@service. Sans elle, la clé peut "
           "encore ouvrir un terminal interactif, ce qui vide la commande "
           "forcée de son sens. Les deux options vont dans le même key_options.",
    )


# === Cle restreinte de bob ===

def test_bob_has_restricted_key(host):
    content = host.file("/home/bob/.ssh/authorized_keys").content_string
    assert "bob@laptop" in content, message(
        en="bob's key is not deployed. Read files/bob.pub.key.pub, the PUBLIC "
           "one despite the name.",
        fr="La clé de bob n'est pas déployée. Lis files/bob.pub.key.pub, la "
           "PUBLIQUE malgré son nom.",
    )
    assert f'from="{RESEAU_AUTORISE}"' in content, message(
        en=f"bob's key accepts any source address. Add key_options: "
           f"'from=\"{RESEAU_AUTORISE}\"' to restrict it to the lab network.",
        fr=f"La clé de bob accepte n'importe quelle adresse source. Ajoute "
           f"key_options: 'from=\"{RESEAU_AUTORISE}\"' pour la restreindre au "
           f"réseau du lab.",
    )
    assert "no-pty" in content, message(
        en="bob's key is missing no-pty. The two options are comma-separated "
           "in a single key_options, not two separate tasks.",
        fr="Il manque no-pty à la clé de bob. Les deux options se séparent par "
           "une virgule dans un seul key_options, et non en deux tâches.",
    )


def test_solution_idempotente():
    """Le second passage du playbook ne doit rien changer (critère RHCE).

    Un playbook qui rejoue et annonce encore des `changed` n'est pas
    idempotent, même si l'état final paraît correct.
    """
    assert_idempotent(__file__)
