# Lab 67 — Tester un rôle sur plusieurs versions d'Ansible avec `tox`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : `pipx install tox` + Molecule (cf. [lab 62](../62-roles-molecule-introduction/)).

## 🧠 Rappel

🔗 [**Tester un rôle Ansible avec tox multi-version**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/tox-multiversion/)

Un rôle distribué sur Galaxy doit fonctionner sur **plusieurs versions
d'`ansible-core`** (typique : 2.16 LTS, 2.17, 2.18). On peut le valider
avec **`tox`**, un orchestrateur d'environnements Python.

```text
tox.ini
   ├─ envlist = ansible-2.{16,17,18}
   ├─ [testenv:ansible-2.16] → pin ansible-core==2.16.* → molecule test
   ├─ [testenv:ansible-2.17] → pin ansible-core==2.17.* → molecule test
   └─ [testenv:ansible-2.18] → pin ansible-core==2.18.* → molecule test
```

`tox` crée 3 venv isolés, installe la version Ansible cible dans chacun,
lance `molecule test`. Si l'un des 3 échoue, c'est qu'un comportement
diverge entre versions — bug de portabilité détecté.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un `tox.ini` avec **plusieurs environnements** Ansible.
2. Pin la version d'`ansible-core` dans chaque env.
3. Lancer `tox -e ansible-2.18` pour une version précise.
4. Lancer `tox` pour **toutes** les versions en parallèle.

## 🔧 Préparation

```bash
pipx install tox
tox --version
```

## ⚙️ Arborescence

```text
labs/tests/tox-multiversion/
├── README.md
├── Makefile
├── tox.ini             ← config tox multi-version
├── roles/webserver/
└── molecule/default/
```

## 📚 Exercice 1 — Lire `tox.ini`

```ini
[tox]
envlist = ansible-2.{16,17,18}

[testenv]
deps =
    molecule
    molecule-plugins[podman]
    pytest-testinfra
commands =
    molecule test

[testenv:ansible-2.16]
deps =
    {[testenv]deps}
    ansible-core>=2.16,<2.17

[testenv:ansible-2.17]
deps =
    {[testenv]deps}
    ansible-core>=2.17,<2.18

[testenv:ansible-2.18]
deps =
    {[testenv]deps}
    ansible-core>=2.18,<2.19
```

🔍 **Observation** :

- **`envlist`** : les noms d'envs à exécuter par défaut.
- **`[testenv]`** : config commune à tous les envs.
- **`[testenv:ansible-2.X]`** : config spécifique avec pin Ansible.
- Hérite de `[testenv]` via `{[testenv]deps}`.

## 📚 Exercice 2 — Lancer une version spécifique

```bash
cd labs/tests/tox-multiversion
tox -e ansible-2.18
```

🔍 `tox` :

1. Crée un venv `.tox/ansible-2.18/`.
2. Installe `ansible-core>=2.18,<2.19` + Molecule + dépendances.
3. Lance `molecule test`.

## 📚 Exercice 3 — Toutes les versions

```bash
tox
```

Lance les 3 envs en série. Sortie résumé :

```text
ansible-2.16: OK
ansible-2.17: OK
ansible-2.18: OK
___________ summary ____________
  ansible-2.16: commands succeeded
  ansible-2.17: commands succeeded
  ansible-2.18: commands succeeded
  congratulations :)
```

## 📚 Exercice 4 — Parallélisation avec `tox-parallel`

```bash
tox -p auto    # parallélise selon le nombre de CPUs
```

🔍 Réduit le temps de test x3 sur une machine 4+ CPU.

## 🔍 Observations à noter

- **`tox`** est l'outil de référence Python pour tester sur plusieurs
  versions de dépendances. Ansible n'est qu'un cas d'usage.
- **Pin strict** (`==2.18.*`) > range large (`>=2.16`). On veut que la
  CI échoue si Ansible publie une nouvelle version qu'on n'a pas
  validée.
- **Idiomatique** dans la communauté Ansible : tous les rôles `geerlingguy`
  sur Galaxy ont un `tox.ini`.
- **Combinable avec CI matrix** (lab 69-70) : GitHub Actions / GitLab
  peuvent lancer `tox -e ansible-X` en parallèle sur des runners séparés.

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

- **`tox-ansible`** plugin : génère automatiquement les envs depuis
  `meta/main.yml` (champs `min_ansible_version` etc.).
- **`tox -e lint`** : ajouter un env qui ne fait que `ansible-lint`,
  séparé des tests Molecule.
- **GitHub Actions matrix** : `strategy.matrix.ansible_version: [2.16,
  2.17, 2.18]` → un runner par version, en parallèle (lab 69).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/tests/tox-multiversion/
```
