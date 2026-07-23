# Lab 67 — Tester un rôle sur plusieurs versions d'Ansible avec `tox`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : `pipx install tox` + Molecule (cf. [lab 62](../../molecule/introduction/)).

## 🧠 Rappel

🔗 [**Tester un rôle Ansible avec tox multi-version**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-tox-multiversion/)

Un rôle distribué sur Galaxy doit fonctionner sur **plusieurs versions
d'`ansible-core`** (typique : 2.19, 2.20, 2.21). On peut le valider
avec **`tox`**, un orchestrateur d'environnements Python.

```text
tox.ini
   ├─ envlist = ansible2.{19,20,21}
   ├─ [testenv:ansible2.19] → pin ansible-core==2.19.* → molecule test
   ├─ [testenv:ansible2.20] → pin ansible-core==2.20.* → molecule test
   └─ [testenv:ansible2.21] → pin ansible-core==2.21.* → molecule test
```

`tox` crée 3 venv isolés, installe la version Ansible cible dans chacun,
lance `molecule test`. Si l'un des 3 échoue, c'est qu'un comportement
diverge entre versions — bug de portabilité détecté.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un `tox.ini` avec **plusieurs environnements** Ansible.
2. Pin la version d'`ansible-core` dans chaque env.
3. Lancer `tox -e ansible2.21` pour une version précise.
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
├── tox.ini             ← config tox multi-version
├── roles/webserver/
└── molecule/default/
```

## 📚 Exercice 1 — Lire `tox.ini`

```ini
[tox]
envlist = ansible2.{19,20,21}
skipsdist = true

[testenv]
commands =
    molecule test

[testenv:ansible2.19]
deps =
    ansible-core==2.19.*
    molecule
    molecule-plugins[podman]
    pytest-testinfra

[testenv:ansible2.20]
deps =
    ansible-core==2.20.*
    molecule
    molecule-plugins[podman]
    pytest-testinfra

[testenv:ansible2.21]
deps =
    ansible-core==2.21.*
    molecule
    molecule-plugins[podman]
    pytest-testinfra
```

🔍 **Observation** :

- **`envlist`** : les noms d'envs à exécuter par défaut.
- **`[testenv]`** : config commune à tous les envs (ici la commande `molecule test`).
- **`[testenv:ansible2.X]`** : config spécifique avec pin Ansible.
- **`deps` est répété en entier dans chaque env, volontairement.** On pourrait
  factoriser les lignes communes avec `{[testenv]deps}`, mais écrire
  `ansible-core==2.X.*` en toutes lettres dans chaque section rend la version
  épinglée lisible d'un coup d'œil, sans dérouler une chaîne de substitutions.
- **`ansible-core==2.19.*`** (pin strict sur la branche), pas `>=2.19,<2.20` :
  une plage large installerait la même dernière version dans les trois envs et
  rendrait la matrice décorative. C'est ce pin que les tests automatisés vérifient.

## 📚 Exercice 2 — Lancer une version spécifique

```bash
cd labs/tests/tox-multiversion
tox -e ansible2.21
```

🔍 `tox` :

1. Crée un venv `.tox/ansible2.21/`.
2. Installe `ansible-core==2.21.*` + Molecule + dépendances.
3. Lance `molecule test`.

## 📚 Exercice 3 — Toutes les versions

```bash
tox
```

Lance les 3 envs en série. Sortie résumé :

```text
ansible2.19: OK
ansible2.20: OK
ansible2.21: OK
___________ summary ____________
  ansible2.19: commands succeeded
  ansible2.20: commands succeeded
  ansible2.21: commands succeeded
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
- **Pin strict** (`==2.21.*`) > range large (`>=2.19`). On veut que la
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
- **GitHub Actions matrix** : `strategy.matrix.ansible_version: [2.19,
  2.20, 2.21]` → un runner par version, en parallèle (lab 69).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/tests/tox-multiversion/
```
