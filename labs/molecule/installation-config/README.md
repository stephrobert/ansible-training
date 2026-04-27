# Lab 63 — Molecule : configuration enrichie

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Molecule installé (cf. [lab 62](../62-roles-molecule-introduction/))
> + Podman/Docker disponible.

## 🧠 Rappel

🔗 [**Molecule : configuration avancée**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/molecule-config/)

Le lab 62 a posé le strict minimum : `molecule.yml`, `converge.yml`, `verify.yml`.
En production, on enrichit avec :

| Fichier | Rôle |
| --- | --- |
| `prepare.yml` | Préparer l'instance (paquets pré-requis, services système) avant `converge` |
| `requirements.yml` | Collections + rôles Galaxy à installer dans l'environnement de test |
| `cleanup.yml` | Nettoyage spécifique avant `destroy` |
| `side_effect.yml` | Tâches "perturbatrices" (down a service, edit config) entre `converge` et `verify` |

Et dans `molecule.yml`, on configure :

- **`provisioner.inventory.host_vars`** : variables par instance.
- **`scenario.test_sequence`** : ordre des étapes du cycle (rajouter `idempotence`).
- **`provisioner.config_options.defaults.callback_enabled`** : callbacks
  Ansible (`profile_tasks`, `timer`).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Ajouter `prepare.yml` qui pré-conditionne l'instance.
2. Ajouter `requirements.yml` qui déclare les dépendances.
3. Configurer `host_vars` dans `molecule.yml` pour personnaliser chaque instance.
4. Définir une `test_sequence` custom incluant `idempotence`.
5. Activer des callbacks `profile_tasks` (perfs).

## 🔧 Préparation

Mêmes pré-requis que le lab 62.

## ⚙️ Arborescence

```text
labs/molecule/installation-config/
├── README.md
├── Makefile
├── roles/
│   └── webserver/
└── molecule/
    └── default/
        ├── molecule.yml          ← config enrichie
        ├── converge.yml
        ├── verify.yml
        ├── prepare.yml           ← NOUVEAU
        └── requirements.yml      ← NOUVEAU
```

## 📚 Exercice 1 — `prepare.yml`

Le `prepare.yml` tourne **avant** `converge.yml`. Idéal pour :

- Installer des paquets manquants dans l'image (curl, ca-certificates).
- Activer des dépôts (epel-release).
- Pré-configurer SELinux ou firewalld.

```yaml
---
- name: Prepare
  hosts: all
  gather_facts: true
  tasks:
    - name: Installer pré-requis pour le rôle webserver
      ansible.builtin.package:
        name:
          - curl
          - ca-certificates
        state: present
```

🔍 **Observation** : `prepare.yml` tourne **une seule fois** au début du
cycle. Si vous le modifiez, relancez `molecule destroy` pour repartir
propre.

## 📚 Exercice 2 — `requirements.yml`

Liste les **collections** et **rôles externes** dont votre rôle dépend
pour les tests :

```yaml
---
collections:
  - name: ansible.posix
    version: ">=2.0.0"
  - name: community.general
    version: ">=10.0.0"

roles:
  - name: geerlingguy.firewall
    version: 3.5.0
```

Molecule installe automatiquement ces dépendances avant `converge`.

🔍 **Observation** : `requirements.yml` est l'**équivalent de `requirements.txt`
en Python**. Bonne pratique pour figer les versions et garantir la
reproductibilité.

## 📚 Exercice 3 — `host_vars` dans `molecule.yml`

```yaml
provisioner:
  name: ansible
  inventory:
    host_vars:
      instance:
        webserver_listen_port: 8080
        webserver_index_content: "Test Molecule custom"
```

🔍 **Observation** : permet de tester **différentes configurations** sans
toucher au rôle. Très utile pour matrix testing.

## 📚 Exercice 4 — `test_sequence` custom

```yaml
scenario:
  test_sequence:
    - dependency
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence       # ← ESSENTIEL : 2ème run = changed=0
    - verify
    - destroy
```

🔍 **Observation** : `idempotence` est **optionnel par défaut**. **Toujours**
l'ajouter — c'est ce qui force la qualité du rôle.

## 📚 Exercice 5 — Callbacks `profile_tasks`

Ajoutez dans `molecule.yml` :

```yaml
provisioner:
  config_options:
    defaults:
      callback_enabled: profile_tasks, timer
```

🔍 **Observation** : à la fin de `converge`, vous voyez **le temps de
chaque tâche** classé par durée. Précieux pour optimiser un rôle lent.

## 🔍 Observations à noter

- **`prepare.yml`** est le bon endroit pour les pré-requis "infrastructure"
  qui ne font pas partie du rôle testé.
- **`requirements.yml`** = reproductibilité. Toujours figer les versions.
- **`host_vars` Molecule** = matrix testing facile sans modifier le rôle.
- **`idempotence` dans `test_sequence`** = qualité non-négociable.
- **`profile_tasks`** = profilage gratuit, à activer en debug.

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

- **Multi-scénarios** : `molecule/default/`, `molecule/cluster/`,
  `molecule/upgrade/` pour tester différents cas. Lancer un scénario
  spécifique : `molecule test -s cluster`.
- **`side_effect.yml`** : entre `converge` et `verify`, simule une panne
  (stop service, suppression fichier) pour tester le rôle de récupération.
- **`MOLECULE_DISTRO`** env var : réutiliser un même `molecule.yml` pour
  tester plusieurs OS via CI matrix (lab 65 + 69).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/molecule/installation-config/
```
