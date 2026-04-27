# Lab 73 — `ansible-galaxy` CLI : tour complet

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Ansible installé. Pas besoin des VMs (lab purement local).

## 🧠 Rappel

🔗 [**ansible-galaxy CLI**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/ansible-galaxy-cli/)

`ansible-galaxy` est l'outil CLI pour **gérer les rôles et collections** :
créer, installer, lister, vérifier, builder, publier. Il y a **2 sous-commandes**
parallèles : `role` et `collection`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Initialiser un nouveau rôle avec `ansible-galaxy role init`.
2. Initialiser une collection avec `ansible-galaxy collection init`.
3. Installer un rôle/collection depuis Galaxy ou Git.
4. Lister ce qui est installé localement.
5. Builder une collection (`.tar.gz`).
6. Publier sur Galaxy avec un token API.
7. Vérifier l'intégrité (`verify`).

## 🔧 Préparation

```bash
ansible-galaxy --version
```

## ⚙️ Arborescence

```text
labs/galaxy/ansible-galaxy-cli/
├── README.md
├── Makefile
├── cheatsheet.md          ← référence rapide des commandes (à étudier)
└── roles/webserver/        ← rôle exemple
```

## 📚 Exercice 1 — Lire `cheatsheet.md`

Le fichier livré couvre toutes les sous-commandes essentielles :

| Commande | Effet |
| --- | --- |
| `ansible-galaxy role init <nom>` | Crée le squelette d'un nouveau rôle |
| `ansible-galaxy collection init <ns.col>` | Crée le squelette d'une collection |
| `ansible-galaxy role install <user.role>` | Installe un rôle depuis Galaxy |
| `ansible-galaxy collection install <user.col>` | Installe une collection depuis Galaxy |
| `ansible-galaxy role install -r requirements.yml` | Installe depuis un fichier de requirements |
| `ansible-galaxy collection install -r requirements.yml` | Idem pour collections |
| `ansible-galaxy role list` | Liste les rôles installés |
| `ansible-galaxy collection list` | Liste les collections installées |
| `ansible-galaxy collection build` | Crée un `.tar.gz` à partir d'une collection |
| `ansible-galaxy collection publish *.tar.gz --token=TOK` | Publie sur Galaxy |
| `ansible-galaxy collection verify <user.col>` | Vérifie l'intégrité (signature) |

## 📚 Exercice 2 — Initialiser un rôle

```bash
cd /tmp
ansible-galaxy role init mon_role
ls mon_role/
# defaults/  files/  handlers/  meta/  README.md  tasks/  templates/  tests/  vars/
```

🔍 **Observation** : 8 dossiers + README + tests/. C'est le **squelette
standard** d'un rôle Galaxy.

## 📚 Exercice 3 — Initialiser une collection

```bash
ansible-galaxy collection init monorg.macollection
ls monorg/macollection/
# docs/  galaxy.yml  meta/  plugins/  README.md  roles/
```

🔍 **Observation** : `galaxy.yml` est le **manifeste** de la collection
(équivalent du `meta/main.yml` d'un rôle, mais pour une collection).

## 📚 Exercice 4 — Installer un rôle

```bash
ansible-galaxy role install geerlingguy.docker
# → ~/.ansible/roles/geerlingguy.docker/

ansible-galaxy role list
# → liste tous les rôles installés avec leur version
```

## 📚 Exercice 5 — Installer une collection

```bash
ansible-galaxy collection install community.docker
# → ~/.ansible/collections/ansible_collections/community/docker/

ansible-galaxy collection list
# → liste toutes les collections installées
```

## 📚 Exercice 6 — Build + Publish d'une collection

```bash
cd monorg/macollection
ansible-galaxy collection build
# → monorg-macollection-1.0.0.tar.gz

ansible-galaxy collection publish monorg-macollection-1.0.0.tar.gz \
    --token=$GALAXY_API_TOKEN
```

🔍 **Observation** : pour publier, il faut un **token Galaxy** (compte sur
[galaxy.ansible.com](https://galaxy.ansible.com/) → Preferences → API Key).

## 🔍 Observations à noter

- **Rôle vs Collection** : un rôle est plus simple (un seul rôle), une
  collection peut grouper rôles + plugins + modules + docs.
- **Galaxy 2026** privilégie les **collections** sur les rôles seuls. Un
  rôle isolé peut être encapsulé dans une collection pour la
  publication.
- **`requirements.yml`** est l'équivalent de `package.json` Node ou
  `requirements.txt` Python. Couvert au lab 74.
- **`collection verify`** : vérifie l'intégrité (hash). Important si
  vous distribuez via un repo privé.

## 🤔 Questions de réflexion

1. Comment adapter votre solution si la cible passait de **1 host** à un
   parc de **50 serveurs** ? Quels paramètres (`forks`, `serial`, `strategy`)
   faudrait-il ajuster pour conserver des temps d'exécution acceptables ?

2. Quels modules Ansible alternatifs auriez-vous pu utiliser pour atteindre
   le même résultat ? Quels sont leurs trade-offs (idempotence garantie,
   performance, dépendances de collection externe) ?

3. Si une étape du playbook échoue en cours d'exécution, quel est l'impact
   sur les hôtes déjà traités ? Comment rendre le scénario reprenable
   (`block/rescue/always`, `--start-at-task`, `serial`) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`--ignore-errors`** : continue malgré une erreur sur un des items
  (utile en CI).
- **`--force`** : réinstalle même si déjà présent.
- **`--namespace`** : préfixe de namespace (vous pouvez avoir plusieurs).
- **Token dans `~/.ansible.cfg`** au lieu de `--token=` :
  `[galaxy] server_list = primary; [galaxy_server.primary]
  url=https://galaxy.ansible.com/ token=...`.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/galaxy/ansible-galaxy-cli/
```
