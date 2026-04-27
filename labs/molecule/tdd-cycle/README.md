# Lab 64 — Molecule : cycle TDD complet

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Molecule installé (cf. [lab 62](../62-roles-molecule-introduction/)).

## 🧠 Rappel

🔗 [**Cycle TDD avec Molecule**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/molecule-tdd/)

**TDD (Test-Driven Development)** appliqué à un rôle Ansible :

```text
1. Écrire les assertions (verify.yml) — RED (les tests échouent)
2. Écrire les tâches du rôle (tasks/main.yml) — minimum pour passer
3. molecule test → GREEN (les assertions passent)
4. Refactor (améliorer le code sans casser les tests)
```

Ce lab démontre le cycle TDD sur un **nouveau rôle `users`** (créer des
utilisateurs depuis une liste de dicts).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Démarrer un rôle par les **tests** (`verify.yml`).
2. Écrire un `argument_specs.yml` qui **précède** le code.
3. Itérer : écrire la tâche minimale → `molecule converge` → ajuster.
4. Refactorer en gardant les tests verts.

## 🔧 Préparation

Mêmes pré-requis que le lab 62 (Molecule + Podman).

## ⚙️ Arborescence

```text
labs/molecule/tdd-cycle/
├── README.md
├── Makefile
├── roles/
│   └── users/                            ← NOUVEAU rôle (créé en TDD)
│       ├── tasks/main.yml                ← itère sur users_to_create
│       ├── defaults/main.yml             ← users_to_create par défaut
│       └── meta/
│           ├── main.yml
│           └── argument_specs.yml        ← définit users_to_create (list of dicts)
└── molecule/
    └── default/
        ├── molecule.yml
        ├── converge.yml                  ← passe users_to_create custom (avec alice/zsh)
        └── verify.yml                    ← ≥4 assertions (cycle TDD)
```

## 📚 Exercice 1 — `verify.yml` d'abord (étape RED)

```yaml
---
- name: Verify users role
  hosts: all
  become: true
  tasks:
    - name: Vérifier qu'alice existe
      ansible.builtin.getent:
        database: passwd
        key: alice
    - ansible.builtin.assert:
        that:
          - getent_passwd['alice'] is defined
        fail_msg: "alice n'existe pas"

    - name: Vérifier que le shell d'alice est /bin/zsh
      ansible.builtin.assert:
        that:
          - getent_passwd['alice'][5] == '/bin/zsh'
        fail_msg: "alice n'a pas /bin/zsh"

    # ... 2 autres assertions au moins ...
```

🔍 **Observation** : on commence par **lister les comportements attendus**
sous forme d'assertions. Sans le rôle, ces assertions échouent.

## 📚 Exercice 2 — `argument_specs.yml`

Avant de coder, on déclare le contrat d'entrée du rôle :

```yaml
argument_specs:
  main:
    options:
      users_to_create:
        type: list
        elements: dict
        required: true
        description: Liste de dicts avec name + shell + (optionnel) groups
        options:
          name:
            type: str
            required: true
          shell:
            type: str
            default: /bin/bash
          groups:
            type: list
            elements: str
            required: false
```

🔍 **Observation** : ce fichier sert de **documentation exécutable** et
**garde-fou**. Le rôle refusera tout appel mal formé.

## 📚 Exercice 3 — `tasks/main.yml` minimal (étape GREEN)

```yaml
---
- name: Créer les utilisateurs
  ansible.builtin.user:
    name: "{{ item.name }}"
    shell: "{{ item.shell | default('/bin/bash') }}"
    groups: "{{ item.groups | default(omit) }}"
    append: "{{ 'true' if item.groups is defined else omit }}"
    state: present
  loop: "{{ users_to_create }}"
  loop_control:
    label: "{{ item.name }}"
```

🔍 **Observation** : un `loop:` sur la liste, avec `default(omit)` pour
les champs optionnels.

## 📚 Exercice 4 — Lancer le cycle complet

```bash
cd labs/molecule/tdd-cycle
molecule test
```

Étapes :

1. `create` : conteneur lancé.
2. `converge` : rôle `users` appliqué — alice, bob créés.
3. `idempotence` : 2ème run, `changed=0`.
4. `verify` : assertions passent → ✅.

Si une assertion échoue, c'est que le rôle ne fait pas (encore) ce qui
est demandé. **Cycle TDD** : on corrige le rôle, on relance.

## 🔍 Observations à noter

- **TDD = écrire les tests AVANT le code**. C'est contre-intuitif au
  début mais rend le rôle **prouvablement correct**.
- **`argument_specs.yml`** est aussi une forme de test (validation
  d'entrée).
- **Pattern `loop` + `default(omit)`** : standard pour des rôles qui
  acceptent des listes de configs avec champs optionnels.
- **Refactor sans peur** : tant que `molecule test` passe, vous pouvez
  réécrire le rôle (renommer variables, factorer) en sécurité.

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

- **`molecule converge` + édition** : itérer rapidement sans recréer le
  conteneur à chaque fois.
- **`molecule verify` seul** : relance juste les assertions après une
  modif de tâche.
- **Mutation testing** : casser volontairement une tâche pour vérifier
  que les tests détectent. Si un test ne casse pas, il manque une
  assertion.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/molecule/tdd-cycle/roles/users/
```
