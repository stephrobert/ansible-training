# Lab 36 — Module `package:` (installation agnostique multi-distro)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Module package Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-package/)

`ansible.builtin.package:` installe des paquets de manière **agnostique** : Ansible
détecte automatiquement le gestionnaire (`ansible_pkg_mgr`) et appelle `dnf:` sur
RHEL, `apt:` sur Debian, `pacman:` sur Arch, `zypper:` sur SUSE. Idéal pour des
**rôles multi-distros**.

Sur un parc 100% RHEL/RockyLinux/AlmaLinux, préférer **`dnf:`** (lab 37) qui
expose des options spécifiques (`enablerepo`, `security`, `bugfix`).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Installer** un ou plusieurs paquets en une seule tâche.
2. **Distinguer** `state: present` vs `state: latest` (et leurs risques).
3. **Désinstaller** des paquets pour le durcissement (CIS Benchmark).
4. **Comparer** la performance d'une **liste** vs `loop:` (ratio 4×).
5. **Identifier** les cas où `package:` ne suffit plus (passage à `dnf:`).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "dnf -y remove tree htop ncdu telnet 2>/dev/null; true"
```

## 📚 Exercice 1 — Installation d'un paquet unique

Créez `lab.yml` :

```yaml
---
- name: Demo package simple
  hosts: web1.lab
  become: true
  tasks:
    - name: Installer vim-enhanced
      ansible.builtin.package:
        name: vim-enhanced
        state: present
```

**Lancez** :

```bash
ansible-playbook labs/modules-paquets/package/lab.yml
ssh ansible@web1.lab 'rpm -q vim-enhanced && which vim'
```

🔍 **Observation** :

- Premier run : `changed=1` (installation).
- Deuxième run : `changed=0` (déjà installé — idempotent).
- Le binaire `vim` est dans `/usr/bin/` après installation.

## 📚 Exercice 2 — Liste de paquets (1 tâche, N installations)

```yaml
- name: Installer plusieurs paquets en une fois
  ansible.builtin.package:
    name:
      - vim-enhanced
      - bash-completion
      - tree
      - htop
      - ncdu
    state: present
```

**Comparez les deux approches** (liste vs loop) :

```yaml
# A : liste (1 appel dnf, 5 paquets)
- ansible.builtin.package:
    name: [vim-enhanced, bash-completion, tree, htop, ncdu]
    state: present

# B : loop (5 appels dnf, 1 paquet chaque)
- ansible.builtin.package:
    name: "{{ item }}"
    state: present
  loop: [vim-enhanced, bash-completion, tree, htop, ncdu]
```

**Lancez** et comparez les durées :

```bash
time ansible-playbook labs/modules-paquets/package/lab.yml
```

🔍 **Observation** : la version **liste** est **3-5× plus rapide** que la version
loop. Une seule transaction `dnf install pkg1 pkg2 pkg3 ...` au lieu de 5
transactions séparées (résolution de dépendances, lock yum, etc.).

**Règle** : pour des paquets **indépendants**, **toujours** la liste.

## 📚 Exercice 3 — `state: present` vs `state: latest`

```yaml
- name: present (installe si absent, ne mets PAS a jour)
  ansible.builtin.package:
    name: tree
    state: present

- name: latest (installe ET met a jour vers la derniere version)
  ansible.builtin.package:
    name: tree
    state: latest
```

| `state:` | Comportement | Risque |
|---|---|---|
| `present` (défaut) | Installe si absent, **n'upgrade pas** | Faible |
| `latest` | Installe **et upgrade systématiquement** | **Mise à jour non maîtrisée** en prod |
| `absent` | Désinstalle si présent | Faible (idempotent) |

🔍 **Observation** : `state: latest` est **dangereux** sur un paquet critique en
prod — chaque run peut faire un upgrade silencieux. Préférer `state: present` +
**cycle de patching dédié** (`dnf:` avec `security: true`).

## 📚 Exercice 4 — Désinstallation pour durcissement (CIS)

Le **CIS Benchmark** demande de désinstaller plusieurs paquets dangereux par
défaut sur RHEL.

```yaml
- name: Durcissement CIS - retirer paquets dangereux
  ansible.builtin.package:
    name:
      - telnet
      - rsh
      - ypbind
      - tftp
      - xinetd
    state: absent
```

🔍 **Observation** : `state: absent` est **idempotent** — si le paquet n'est pas
installé, tâche `ok`. Si installé, désinstallation propre. Pattern
**audit-friendly** : à chaque run, on vérifie que ces paquets sont bien absents.

**`telnet`** est la cible n°1 — protocole en clair, équivalent SSH des années 90.

## 📚 Exercice 5 — `use:` (forcer le gestionnaire)

Par défaut, Ansible auto-détecte (`use: auto`). Vous pouvez forcer :

```yaml
- name: Forcer dnf meme si Ansible detecte autre chose
  ansible.builtin.package:
    name: htop
    state: present
    use: dnf
```

🔍 **Observation** : utile sur des **images Docker exotiques** où plusieurs
gestionnaires coexistent (rare mais arrive). Par défaut, ne rien spécifier — la
détection automatique marche dans 99% des cas.

## 📚 Exercice 6 — Le piège : nom de paquet différent selon la distro

Le module `package:` est agnostique sur le **gestionnaire**, mais **pas sur les
noms de paquets** !

| Sur RHEL | Sur Debian |
|---|---|
| `httpd` | `apache2` |
| `mariadb-server` | `mariadb-server` |
| `python3` | `python3` |
| `vim-enhanced` | `vim` |
| `dnf-utils` | (n/a) |

```yaml
# ❌ Ne marche que sur RHEL
- ansible.builtin.package:
    name: httpd
    state: present

# ✅ Pattern multi-distro
- ansible.builtin.package:
    name: "{{ apache_package_name }}"
    state: present
  vars:
    apache_package_name: "{{ 'httpd' if ansible_os_family == 'RedHat' else 'apache2' }}"
```

🔍 **Observation** : le module est **multi-distro**, mais **vous** devez gérer la
correspondance des noms via `when:`, `vars:`, ou des `group_vars/<distribution>.yml`.

## 📚 Exercice 7 — Quand `package:` ne suffit plus

`package:` n'expose **que les options communes**. Pour ces cas, passer à `dnf:`
ou `apt:` directement :

| Besoin | Module |
|---|---|
| Activer un repo temporairement | `dnf: enablerepo:` |
| Mises à jour de **sécurité** uniquement | `dnf: security: true` |
| Update cache (refresh repos) | `dnf: update_cache:` |
| Installation **groupes** (`@web-server`) | `dnf: name: '@web-server'` |
| Pré-télécharger sans installer | `dnf: download_only:` |

🔍 **Observation** : ces options sont **spécifiques** à `dnf` (RHEL) ou `apt`
(Debian). Pour les utiliser, abandonner `package:` au profit du module spécifique.

## 🔍 Observations à noter

- **`package:`** = multi-distro (auto-détection du gestionnaire).
- **Liste de paquets** dans `name:` est **3-5× plus rapide** qu'une boucle.
- **`state: latest`** est dangereux en prod — préférer `present` + cycle de patching.
- **`state: absent`** = outil de **durcissement** (CIS Benchmark).
- **Noms de paquets diffèrent** entre distros (`httpd` vs `apache2`).
- **`package:` n'expose pas** `enablerepo`, `security`, `update_cache` — passer à `dnf:` (lab 37).

## 🤔 Questions de réflexion

1. Vous écrivez un rôle pour **AlmaLinux + Ubuntu**. Quelle structure pour gérer
   les noms de paquets différents ? (indice : `vars:` + `ansible_os_family`).

2. Un collègue propose `state: latest` sur tous les paquets "pour avoir les
   dernières versions". Quels sont les **3 risques** en prod ?

3. Quand passer de `package:` à `dnf:` directement ? Donnez **3 cas
   spécifiques**.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`package_facts:`** : module qui retourne **tous les paquets installés** sur
  le managed node (en dict). Utile pour audit ou conditionnel.
- **`dnf:`** (lab 37) : version spécifique RHEL avec options avancées.
- **`apt:`** : équivalent Debian — options `update_cache`, `cache_valid_time`.
- **Pattern `package_install_pre`** : un play d'audit qui collecte les paquets
  manquants avant un grand deploy, pour ne lancer que les installations
  nécessaires.
- **`yum:`** : alias **legacy** de `dnf:` — fonctionne mais déprécié sur RHEL 8+.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-paquets/package/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-paquets/package/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-paquets/package/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
