# Lab 65 — Molecule : scénarios multi-distro

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis : Molecule + Podman/Docker installés (cf. [lab 62](../62-roles-molecule-introduction/)).

## 🧠 Rappel

🔗 [**Tester un rôle Ansible sur plusieurs distributions**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/molecule-multi-distro/)

Un rôle prêt pour Galaxy doit fonctionner sur **plusieurs OS** : RHEL,
AlmaLinux, Rocky, Debian, Ubuntu, parfois SUSE. Molecule rend ça **simple**
en ajoutant des plateformes dans `molecule.yml`.

Le **secret de la portabilité** : utiliser des **abstractions par OS** dans
le rôle :

| Élément | Pattern multi-OS |
| --- | --- |
| Module paquet | `ansible.builtin.package:` (pas `dnf:` ni `apt:`) |
| Nom du paquet | Variable `__webserver_package` chargée selon `ansible_os_family` |
| User système | Variable `__webserver_user` (`nginx` sur RHEL, `www-data` sur Debian) |
| Dossier HTML | Variable `__webserver_html_dir` (`/usr/share/nginx/html` vs `/var/www/html`) |
| Service | Variable `__webserver_service` (généralement identique) |

Ces variables vivent dans `vars/<OS>.yml` et sont chargées dynamiquement par
`include_vars` au démarrage du rôle.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Tester un rôle sur **3 distributions** différentes (RHEL/Alma + Debian + Ubuntu).
2. Charger dynamiquement `vars/{{ ansible_os_family }}.yml`.
3. Utiliser `ansible.builtin.package:` (agnostique).
4. Diverger les chemins / noms de paquets / users entre OS.
5. Vérifier que le **même rôle** fonctionne sur les 3 OS via Molecule.

## 🔧 Préparation

```bash
podman --version  # ou docker
molecule --version
```

## ⚙️ Arborescence

```text
labs/molecule/scenarios-multi-distro/
├── README.md
├── Makefile
├── roles/
│   └── webserver/
│       ├── tasks/main.yml          ← include_vars dynamique + package agnostique
│       ├── defaults/main.yml
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       ├── vars/
│       │   ├── RedHat.yml          ← vars spécifiques RedHat/Alma/Rocky
│       │   └── Debian.yml          ← vars spécifiques Debian/Ubuntu
│       └── templates/nginx.conf.j2
└── molecule/
    └── default/
        ├── molecule.yml            ← ≥3 platforms (RHEL + Debian + Ubuntu)
        ├── converge.yml
        └── verify.yml
```

## 📚 Exercice 1 — `vars/RedHat.yml` vs `vars/Debian.yml`

```yaml
# vars/RedHat.yml
__webserver_package: nginx
__webserver_user: nginx
__webserver_html_dir: /usr/share/nginx/html
__webserver_service: nginx
```

```yaml
# vars/Debian.yml
__webserver_package: nginx
__webserver_user: www-data
__webserver_html_dir: /var/www/html
__webserver_service: nginx
```

🔍 **Observation** — convention `__nom_de_var` (double underscore préfixe)
indique : variable **interne au rôle**, ne pas la surcharger côté
utilisateur.

## 📚 Exercice 2 — `tasks/main.yml` avec `include_vars` dynamique

```yaml
---
- name: Charger les variables OS-specific
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"

- name: Installer le paquet (agnostique)
  ansible.builtin.package:
    name: "{{ __webserver_package }}"
    state: present

- name: Déployer la page d'accueil dans le bon dossier
  ansible.builtin.copy:
    dest: "{{ __webserver_html_dir }}/index.html"
    content: "Hello from {{ ansible_distribution }}\n"
    mode: "0644"
    owner: "{{ __webserver_user }}"
```

🔍 **Observation** :

- `ansible.builtin.package:` choisit `dnf`/`apt`/`zypper` selon l'OS.
- `{{ ansible_os_family }}` vaut `RedHat` ou `Debian` — match exact avec
  les fichiers `vars/`.
- `include_vars` (dynamique) > `vars_files` (statique) car ne marche pas
  dans un rôle.

## 📚 Exercice 3 — `molecule.yml` avec 3 plateformes

```yaml
platforms:
  - name: instance-rhel
    image: quay.io/centos/centos:stream10
    pre_build_image: true

  - name: instance-debian
    image: docker.io/library/debian:12
    pre_build_image: true

  - name: instance-ubuntu
    image: docker.io/library/ubuntu:24.04
    pre_build_image: true
```

🔍 **Observation** : Molecule crée **3 conteneurs en parallèle**, applique
le rôle, vérifie sur chacun. Si l'un des 3 échoue, le test entier échoue.

## 📚 Exercice 4 — Lancer

```bash
cd labs/molecule/scenarios-multi-distro
molecule test
```

🔍 Vous voyez 3 instances `converge` en parallèle, chaque distrib avec son
chemin/user/paquet propre. La sortie liste les 3 instances dans le PLAY
RECAP.

## 🔍 Observations à noter

- **Module `package:`** est l'arme principale du multi-OS. Préférez-le à
  `dnf:`/`apt:` sauf si vous avez besoin d'options spécifiques.
- **`vars/<OS_family>.yml`** + `include_vars` = pattern standard. Marche
  même pour des OS très différents.
- **3+ plateformes** dans `molecule.yml` = vraie matrice de test.
- **Convention `__var`** : variables internes du rôle. Ne **pas** mettre
  dans `defaults/` (que l'utilisateur peut override) — mettre dans `vars/`.

## 🤔 Questions de réflexion

1. Vous voulez ajouter **SUSE** (`opensuse/leap`) à la matrice. Quelle est
   la valeur de `ansible_os_family` pour SUSE ? Quel `vars/<OS>.yml`
   créer ?

2. Sur Debian, le service `nginx` ne démarre pas après installation
   (différent de RHEL). Comment forcer le démarrage **uniquement sur
   Debian** ?

3. Vous voulez tester **2 versions** d'AlmaLinux (9 et 10). Combien de
   plateformes dans `molecule.yml` ? Comment les nommer pour les
   distinguer ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`group_by` Ansible** : créer dynamiquement des groupes basés sur
  `ansible_os_family`, puis appliquer des tâches `when:` plus simples.
- **`ansible_distribution_major_version`** : différencier RHEL 9 vs RHEL 10.
- **Images CI** : `quay.io/jeffwecan/molecule-rhel:9` et autres images
  optimisées pour Molecule (avec systemd).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile production labs/molecule/scenarios-multi-distro/
```
