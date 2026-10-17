"""Tests pytest+testinfra pour le challenge module file.

Chaque assertion porte un message, et dans les deux langues. Ce n'est pas une
politesse : depuis dsoxlab 0.4.0, `dsoxlab check` n'affiche plus le traceback de
pytest mais le **nom des tests en échec et le message que l'auteur a écrit**.
Sans message, l'apprenant lit « release dir exists » et rien sur ce qu'il doit
corriger.

Tout le reste du lab existe en deux versions (`README.md` et `README.fr.md`) ;
ce fichier ne peut pas, son nom étant imposé par le contrat. D'où `message()`,
fourni par le `conftest.py` du dépôt, qui choisit selon `DSOXLAB_LANG`.

Un message dit trois choses : ce qui est attendu, ce qui a été trouvé, et le
geste qui corrige.
"""

import pytest

from conftest import lab_host, message

TARGET_HOST = "web1.lab"

RELEASE = "/opt/myapp/releases/v1.0.0"
LOGS = "/opt/myapp/shared/logs"
CURRENT = "/opt/myapp/current"
OLD_CONF = "/etc/myapp-old.conf"
TIMESTAMP = "/var/log/myapp-init.timestamp"


@pytest.fixture(scope="module")
def host():
    return lab_host(TARGET_HOST)


# === Repertoire de release ===

def test_release_dir_exists(host):
    f = host.file(RELEASE)
    assert f.exists, message(
        en=f"{RELEASE} is missing. This is the challenge's first task: "
           f"ansible.builtin.file with state: directory.",
        fr=f"{RELEASE} est absent. C'est la première tâche du challenge : "
           f"ansible.builtin.file avec state: directory.",
    )
    assert f.is_directory, message(
        en=f"{RELEASE} exists but is not a directory. With state: touch or "
           f"state: file the module creates a file: use state: directory.",
        fr=f"{RELEASE} existe mais n'est pas un répertoire. Avec state: touch ou "
           f"state: file, le module crée un fichier : il faut state: directory.",
    )
    assert f.mode == 0o755, message(
        en=f"{RELEASE} is {oct(f.mode)}, expected 0755. Set mode: \"0755\" "
           f"in quotes, otherwise YAML reads 755 as decimal.",
        fr=f"{RELEASE} est en {oct(f.mode)}, attendu 0755. Pose mode: \"0755\" "
           f"entre guillemets, sinon YAML lit 755 en décimal.",
    )
    assert f.user == "root", message(
        en=f"{RELEASE} is owned by {f.user}, expected root. Add owner: root, "
           f"and check the task runs with become: true.",
        fr=f"{RELEASE} appartient à {f.user}, attendu root. Ajoute owner: root, "
           f"et vérifie que la tâche tourne avec become: true.",
    )


# === Repertoire de logs ===

def test_logs_dir_exists(host):
    f = host.file(LOGS)
    assert f.exists, message(
        en=f"{LOGS} is missing. Second task: a second ansible.builtin.file "
           f"with state: directory.",
        fr=f"{LOGS} est absent. Deuxième tâche du challenge : un second "
           f"ansible.builtin.file avec state: directory.",
    )
    assert f.is_directory, message(
        en=f"{LOGS} exists but is not a directory: use state: directory.",
        fr=f"{LOGS} existe mais n'est pas un répertoire : il faut state: directory.",
    )
    assert f.mode == 0o750, message(
        en=f"{LOGS} is {oct(f.mode)}, expected 0750. That mode denies all "
           f"access to other users, which is what a log directory wants.",
        fr=f"{LOGS} est en {oct(f.mode)}, attendu 0750. Ce mode retire tout droit "
           f"aux autres utilisateurs, ce qu'on attend d'un répertoire de logs.",
    )
    assert f.user == "nobody", message(
        en=f"{LOGS} is owned by {f.user}, expected nobody. Add owner: nobody.",
        fr=f"{LOGS} appartient à {f.user}, attendu nobody. Ajoute owner: nobody.",
    )
    assert f.group == "nobody", message(
        en=f"{LOGS} has group {f.group}, expected nobody. owner: does not set "
           f"the group: you also need group: nobody.",
        fr=f"{LOGS} a le groupe {f.group}, attendu nobody. owner: ne pose pas le "
           f"groupe : il faut aussi group: nobody.",
    )


# === Lien symbolique current ===

def test_current_is_symlink(host):
    f = host.file(CURRENT)
    assert f.exists, message(
        en=f"{CURRENT} is missing. Third task: state: link, with src: the "
           f"release and dest: this path.",
        fr=f"{CURRENT} est absent. Troisième tâche : state: link, avec src: la "
           f"release et dest: ce chemin.",
    )
    assert f.is_symlink, message(
        en=f"{CURRENT} exists but is not a symbolic link. state: file and "
           f"state: touch create an ordinary file: use state: link.",
        fr=f"{CURRENT} existe mais n'est pas un lien symbolique. state: file ou "
           f"state: touch crée un fichier ordinaire : il faut state: link.",
    )
    assert f.linked_to == RELEASE, message(
        en=f"{CURRENT} points at {f.linked_to}, expected {RELEASE}. src: names "
           f"the link's target, dest: where the link itself goes.",
        fr=f"{CURRENT} pointe sur {f.linked_to}, attendu {RELEASE}. C'est src: "
           f"qui désigne la cible du lien, et dest: l'emplacement du lien.",
    )


# === Suppression conf obsolete ===

def test_old_conf_absent(host):
    assert not host.file(OLD_CONF).exists, message(
        en=f"{OLD_CONF} is still there. Fourth task: state: absent removes it, "
           f"and does not fail when the file was already gone.",
        fr=f"{OLD_CONF} est encore là. Quatrième tâche : state: absent le "
           f"supprime, et ne lève pas si le fichier n'existait déjà pas.",
    )


# === Touch timestamp ===

def test_timestamp_exists(host):
    f = host.file(TIMESTAMP)
    assert f.exists, message(
        en=f"{TIMESTAMP} is missing. Fifth task: state: touch, the module's "
           f"only state that CREATES an empty file. state: file does not.",
        fr=f"{TIMESTAMP} est absent. Cinquième tâche : state: touch, le seul état "
           f"du module qui CRÉE un fichier vide. state: file ne le crée pas.",
    )
    assert f.is_file, message(
        en=f"{TIMESTAMP} exists but is not an ordinary file: state: touch expected.",
        fr=f"{TIMESTAMP} existe mais n'est pas un fichier ordinaire : state: touch "
           f"attendu.",
    )
    assert f.mode == 0o644, message(
        en=f"{TIMESTAMP} is {oct(f.mode)}, expected 0644. state: touch takes "
           f"mode: like the other states.",
        fr=f"{TIMESTAMP} est en {oct(f.mode)}, attendu 0644. state: touch accepte "
           f"mode: comme les autres états.",
    )

# Pas de test d'idempotence ici, volontairement.
# Ce lab démontre que `state: touch` N'EST PAS idempotent (il réécrit le
# mtime à chaque passage) : c'est justement sa leçon, et son README le dit.
# Exiger changed=0 ici contredirait ce que le lab enseigne.
