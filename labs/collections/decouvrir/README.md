# Lab 93 — Découvrir les collections Ansible (FQCN, structure, `ansible-galaxy`)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Découvrir les collections Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/)

Une **collection** est l'unité de distribution moderne pour les **modules**, **plugins** (filter, lookup, inventory…), **rôles**, **playbooks** et **docs** Ansible. Elle remplace définitivement les rôles standalone Galaxy v1.

Chaque ressource Ansible se nomme désormais avec un **FQCN** (Fully Qualified Collection Name) : **`namespace.collection.plugin`**. Exemples : `ansible.builtin.copy`, `community.general.archive`, `kubernetes.core.k8s`. Ce FQCN devient **obligatoire** sur tous les playbooks RHCE 2026 (règle `fqcn-builtins` d'`ansible-lint --profile production`).

Ce lab explore les collections **déjà installées** dans votre EE / venv : structure, métadonnées, modules disponibles, dépendances entre collections.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Lister** toutes les collections installées (`ansible-galaxy collection list`).
2. **Inspecter** une collection spécifique (`ansible-galaxy collection info`).
3. **Lire** un `galaxy.yml` (métadonnées + dépendances + tags).
4. **Comprendre** la structure standard `plugins/`, `roles/`, `playbooks/`, `meta/runtime.yml`.
5. **Distinguer** un **rôle standalone** d'un **rôle dans une collection**.
6. **Trouver** un module avec son FQCN via `ansible-doc -l | grep`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible-galaxy --version
ansible-galaxy collection install community.general --force 2>&1 | tail -3
```

## ⚙️ Arborescence cible

```text
labs/collections/decouvrir/
├── README.md              ← ce fichier (tuto guidé)
├── Makefile               ← cible clean
└── challenge/
    ├── README.md          ← consigne du challenge
    └── tests/
        └── test_decouvrir.py
```

L'apprenant écrit lui-même `lab.yml` (au fil des exos) et `challenge/solution.yml`.

## 📚 Exercice 1 — Lister les collections installées

```bash
ansible-galaxy collection list
```

Sortie typique :

```text
# /usr/share/ansible/collections/ansible_collections
Collection                    Version
----------------------------- -------
ansible.posix                 2.0.0
community.general             10.5.0
kubernetes.core               5.1.1

# /home/bob/.ansible/collections/ansible_collections
Collection                    Version
----------------------------- -------
community.docker              4.0.0
```

🔍 **Observation** : la commande **agrège** toutes les sources : système (`/usr/share/ansible/`), user (`~/.ansible/`), virtualenv. Plusieurs versions d'une même collection peuvent coexister — celle utilisée dépend de l'ordre dans **`ANSIBLE_COLLECTIONS_PATH`**.

## 📚 Exercice 2 — Inspecter une collection précise

```bash
ansible-galaxy collection info community.general
```

Sortie :

```text
Collection: community.general
Version: 10.5.0
Path: /usr/share/ansible/collections/ansible_collections/community/general
Documentation: https://docs.ansible.com/ansible/latest/collections/community/general/
Repository: https://github.com/ansible-collections/community.general
Issues: https://github.com/ansible-collections/community.general/issues
License: GPL-3.0-or-later
Authors:
  - Ansible Community
```

🔍 **Observation** : c'est l'équivalent de `dnf info` ou `apt show`. **Référence** pour vérifier qu'une collection vient bien de Galaxy public et pas d'une source compromise.

## 📚 Exercice 3 — Lire le `galaxy.yml`

```bash
cat /usr/share/ansible/collections/ansible_collections/community/general/galaxy.yml | head -30
```

Champs clés :

| Champ | Rôle |
|-------|------|
| `namespace` | Préfixe du FQCN (ex: `community`, `kubernetes`, `acme`) |
| `name` | Nom court de la collection |
| `version` | Semver strict (ex: `10.5.0`) |
| `dependencies` | Autres collections requises (avec contraintes de version) |
| `tags` | Catégories (`linux`, `web`, `cloud`, `kubernetes`) |
| `repository` | URL du repo Git source |
| `documentation` | URL de la doc générée |

🔍 **Observation** : `tags:` est **obligatoire** pour publier sur Galaxy. Sans tags, l'import échoue avec un message peu explicite.

## 📚 Exercice 4 — Explorer la structure interne

```bash
tree -L 2 /usr/share/ansible/collections/ansible_collections/community/general/
```

Sortie typique :

```text
community.general/
├── galaxy.yml
├── README.md
├── meta/
│   └── runtime.yml
├── plugins/
│   ├── modules/        ← modules Python (ex: archive.py)
│   ├── filter/         ← filtres Jinja2 custom
│   ├── lookup/         ← plugins lookup
│   ├── inventory/      ← plugins d'inventaire
│   └── callback/       ← plugins callback
├── roles/              ← rôles inclus
├── playbooks/          ← playbooks fournis
├── changelogs/
└── docs/
```

🔍 **Observation** : la structure est **fixe** depuis ansible-core 2.10. Un module custom **doit** se trouver dans `plugins/modules/`, jamais à la racine ni dans un `library/` (legacy).

## 📚 Exercice 5 — `meta/runtime.yml` et le seuil ansible-core

```bash
cat /usr/share/ansible/collections/ansible_collections/community/general/meta/runtime.yml | head -10
```

Exemple typique :

```yaml
---
requires_ansible: ">=2.15.0"

plugin_routing:
  modules:
    sudoers:
      redirect: community.general.sudoers
```

🔍 **Observation cruciale** : **`requires_ansible:`** déclare la version minimum d'ansible-core. **`plugin_routing.redirect`** sert quand un module est renommé : un playbook qui utilise l'ancien nom continue de marcher avec un warning de dépréciation. Pattern essentiel pour la rétrocompatibilité.

## 📚 Exercice 6 — Trouver un module via FQCN

```bash
# Lister tous les modules d'une collection
ansible-doc -l community.general | head -10

# Trouver un module par mot-clé
ansible-doc -l | grep -i archive

# Lire la doc d'un module
ansible-doc community.general.archive
```

Sortie :

```text
> COMMUNITY.GENERAL.ARCHIVE    (.../archive.py)

  Creates or extends an archive...

OPTIONS (= is mandatory):
- dest
        The file name of the destination archive...
- format
        The type of compression to use.
        choices:
        - "bz2", "gz", "tar", "xz", "zip"
```

🔍 **Observation** : `ansible-doc <FQCN>` est **la** référence pour vérifier les paramètres avant d'utiliser un module. Préférer à la doc internet — la doc affichée est celle de la **version installée**.

## 📚 Exercice 7 — Différence rôle standalone vs rôle dans collection

Galaxy distribue **deux types** de contenus :

| Type | Distribution | Installation | Usage |
|------|-------------|--------------|-------|
| **Rôle standalone** | `ansible-galaxy role install geerlingguy.docker` | `~/.ansible/roles/geerlingguy.docker/` | `roles: [geerlingguy.docker]` |
| **Rôle dans collection** | `ansible-galaxy collection install community.general` | `~/.ansible/collections/.../community/general/roles/` | `roles: [community.general.bind]` |

🔍 **Observation** : le format **standalone** est **legacy**. Toute nouvelle distribution publie en **collection**. Galaxy NG (backend Galaxy v3, 2026) ne supporte **que** les collections.

## 🔍 Observations à noter

- **FQCN** = `namespace.collection.plugin`, **obligatoire** en 2026.
- **`ansible-galaxy collection list/info`** pour explorer ce qui est installé.
- **`galaxy.yml`** : métadonnées + dépendances + tags.
- **`meta/runtime.yml`** : seuil ansible-core + redirects de modules.
- **Structure fixe** : `plugins/{modules,filter,lookup,inventory,callback}/`, `roles/`, `playbooks/`, `docs/`.
- **`ansible-doc`** : doc de la version installée, plus fiable que internet.

## 🤔 Questions de réflexion

1. Que se passe-t-il si **deux versions** de `community.general` sont installées dans des chemins différents ?

2. Pourquoi le FQCN est-il devenu **obligatoire** alors que les noms courts marchaient avant ?

3. Comment connaître **toutes** les collections **dépendances** d'une collection donnée ?

4. À quoi sert **`build_ignore:`** dans `galaxy.yml` ? (Indice : exclure `.git/`, `.venv/`, secrets de tests du tarball publié).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — produire un fichier d'inventaire des collections installées avec **leurs versions** et leurs **dépendances**, déposé sur `db1.lab`.

## 💡 Pour aller plus loin

- **Lab 94** : `requirements.yml` complet (Galaxy + Git + signatures GPG).
- **Lab 95** : créer **votre propre collection** avec `ansible-galaxy collection init`.
- **Galaxy public vs Automation Hub** : deux registres, deux écosystèmes.
- **Validated Content Red Hat** : collections **certifiées + signées + scannées Trivy**.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/collections/decouvrir/lab.yml
ansible-lint labs/collections/decouvrir/challenge/solution.yml
ansible-lint --profile production labs/collections/decouvrir/challenge/solution.yml
```

> 💡 **Astuce** : la règle **`fqcn-builtins`** d'ansible-lint signale tout module utilisé sans FQCN. Indispensable pour préparer la RHCE.
