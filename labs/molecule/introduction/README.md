# Lab 62 — Molecule : introduction

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : `pipx install molecule molecule-plugins[podman]` (ou `[docker]`)
> et **podman/docker** disponibles. Pas besoin des VMs Ansible — Molecule
> teste dans des conteneurs locaux.

## 🧠 Rappel

🔗 [**Tester un rôle Ansible avec Molecule**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/molecule-introduction/)

**Molecule** est l'outil de référence pour **tester les rôles Ansible**. Il
automatise un cycle complet :

```text
create → prepare → converge → idempotence → verify → destroy
```

| Étape | Effet |
| --- | --- |
| `create` | Crée un conteneur (Podman/Docker) ou une VM |
| `prepare` | Installe les pré-requis dans l'instance |
| `converge` | Applique le rôle (= `ansible-playbook converge.yml`) |
| `idempotence` | Relance pour vérifier `changed=0` |
| `verify` | Lance les assertions (verify.yml) |
| `destroy` | Détruit l'instance |

**Cycle TDD** : on écrit les `verify.yml` (assertions) **avant** d'écrire les
tâches du rôle. Quand `verify` passe, le rôle fonctionne.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Comprendre l'arborescence d'un scénario Molecule (`molecule/default/`).
2. Lire `molecule.yml`, `converge.yml`, `verify.yml`.
3. Identifier le **driver** (Podman, Docker, delegated, default).
4. Identifier les **plateformes** de test (instances à créer).
5. Identifier le **verifier** (Ansible-assert ou testinfra).

## 🔧 Préparation

```bash
pipx install molecule
pipx inject molecule molecule-plugins[podman]
podman --version       # ou docker --version
molecule --version
```

## ⚙️ Arborescence du lab

```text
labs/molecule/introduction/
├── README.md
├── Makefile
├── roles/
│   └── webserver/                    ← rôle à tester (livré)
└── molecule/
    └── default/                      ← scénario "default" (livré)
        ├── molecule.yml              ← config Molecule (driver, platforms, verifier)
        ├── converge.yml              ← play qui applique le rôle
        └── verify.yml                ← assertions post-converge
```

## 📚 Exercice 1 — Lire `molecule/default/molecule.yml`

```bash
cat labs/molecule/introduction/molecule/default/molecule.yml
```

🔍 **Observation** — 4 sections obligatoires :

```yaml
driver:
  name: podman              # ou docker, default, delegated

platforms:
  - name: instance-rhel
    image: quay.io/centos/centos:stream10
    privileged: true
    pre_build_image: true

provisioner:
  name: ansible             # toujours ansible

verifier:
  name: ansible             # ou testinfra
```

## 📚 Exercice 2 — Lire `converge.yml`

C'est le play qui **applique le rôle** sur l'instance créée :

```yaml
---
- name: Converge - apply webserver role
  hosts: all
  become: true
  roles:
    - role: webserver
```

🔍 **Observation** : `hosts: all` cible **les instances Molecule** (pas vos
managed nodes du lab Ansible). Molecule génère son propre inventaire à la
volée.

## 📚 Exercice 3 — Lire `verify.yml`

```yaml
---
- name: Verify
  hosts: all
  become: true
  tasks:
    - name: Vérifier que nginx est installé
      ansible.builtin.package_facts:
    - ansible.builtin.assert:
        that:
          - "'nginx' in ansible_facts.packages"
        fail_msg: "nginx n'est pas installé"

    - name: Vérifier que le service tourne
      ansible.builtin.service_facts:
    - ansible.builtin.assert:
        that:
          - ansible_facts.services['nginx.service'].state == 'running'
```

🔍 **Observation** : verify utilise des **assertions Ansible** (mode
`verifier: ansible`). On peut aussi utiliser **testinfra** (mode
`verifier: testinfra`) qui écrit des tests Python — couvert au lab 66.

## 📚 Exercice 4 — Lancer Molecule

```bash
cd labs/molecule/introduction
molecule test
```

🔍 **Sortie attendue** (extrait) :

```text
INFO     Running default > create
...
INFO     Running default > converge
TASK [webserver : Installer nginx] *** changed
...
INFO     Running default > idempotence
TASK [webserver : Installer nginx] *** ok    ← changed=0
...
INFO     Running default > verify
TASK [Vérifier que nginx est installé] *** ok
...
INFO     Running default > destroy
```

Si tout est vert, votre rôle fonctionne **et est idempotent**.

## 🔍 Observations à noter

- **1 lab = 1 scénario Molecule** : le scénario `default/` est le minimum.
  On peut en avoir plusieurs (`default/`, `cluster/`, `upgrade/`) pour
  tester différents cas d'usage.
- **Conteneur ≠ VM** : Molecule + Podman teste très vite (~10-30 s) mais
  sans systemd réel par défaut. Pour tester systemd : `pre_build_image`
  + image Rocky/Alma avec systemd inclus.
- **Idempotence forcée** : Molecule **échoue** si une tâche reste `changed`
  au 2ème run. C'est un garde-fou indispensable.

## 🤔 Questions de réflexion

1. Vous voulez tester votre rôle sur **3 OS** différents (RHEL, Debian,
   Ubuntu). Combien de plateformes déclarez-vous dans `molecule.yml` ?
   (Indice : lab 65.)

2. Le `verify.yml` utilise `verifier: ansible`. Quel est l'avantage
   d'utiliser `verifier: testinfra` à la place ? (Indice : lab 66.)

3. Vous voulez que Molecule **garde** l'instance après `converge` (pour
   inspecter manuellement). Quelle commande utiliser à la place de
   `molecule test` ? (Indice : `molecule converge` + `molecule login`.)

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`molecule converge`** seul : applique sans destroy. Utile pour debug.
- **`molecule login`** : ouvre un shell dans l'instance.
- **`molecule destroy --all`** : nettoie tous les scénarios.
- **`MOLECULE_NO_LOG=false`** : verbose maximum pour debug.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/molecule/introduction/molecule/
ansible-lint --profile production labs/molecule/introduction/
```
