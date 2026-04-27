# Lab 45 — Module `selinux:` et booléens SELinux

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

🔗 [**Module SELinux Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/rhel-systeme/module-selinux/)

SELinux (Security-Enhanced Linux) est le système de **contrôle d'accès
obligatoire** activé par défaut sur RHEL/AlmaLinux/Rocky en mode `enforcing`.
Trois modules Ansible le gèrent :

- **`ansible.posix.selinux:`** — état global (enforcing / permissive / disabled)
  + politique active.
- **`ansible.posix.seboolean:`** — activer/désactiver des **booléens** SELinux
  (`httpd_can_network_connect`, etc.).
- **`community.general.sefcontext:`** — gérer les **contextes** des fichiers
  (avec `restorecon` pour appliquer).

Ces modules sont dans **`ansible.posix`** et **`community.general`** —
`ansible-galaxy collection install ansible.posix community.general`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Vérifier** l'état SELinux et le mode (enforcing / permissive).
2. **Modifier** un **booléen SELinux** avec persistance.
3. **Définir** un contexte custom sur un dossier (`sefcontext` + `restorecon`).
4. **Comprendre** pourquoi un reboot peut être nécessaire (changement de mode).
5. **Diagnostiquer** un service qui plante "à cause de SELinux".

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install ansible.posix community.general
ansible db1.lab -m ping

# Installer les outils Python SELinux (necessaires aux modules)
ansible db1.lab -b -m dnf -a "name=python3-libselinux,policycoreutils-python-utils state=present"

ansible db1.lab -b -m shell -a "rm -rf /var/www/myapp; mkdir -p /var/www/myapp"
```

## 📚 Exercice 1 — Vérifier l'état SELinux

```yaml
---
- name: Demo selinux state
  hosts: db1.lab
  become: true
  tasks:
    - name: Verifier l etat SELinux courant
      ansible.builtin.command: getenforce
      register: enforce
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        msg: |
          Mode SELinux : {{ enforce.stdout }}
          ansible_selinux : {{ ansible_selinux.status | default('unknown') }}
          policy : {{ ansible_selinux.type | default('unknown') }}
```

🔍 **Observation** : `Enforcing` sur AlmaLinux par défaut. Les facts
`ansible_selinux.*` sont collectés automatiquement (`gather_facts: true`).

**3 modes possibles** :

| Mode | Effet |
|---|---|
| `enforcing` | Contraintes appliquées + violations bloquées (production RHEL) |
| `permissive` | Violations **loguées** mais **pas bloquées** (debug) |
| `disabled` | SELinux complètement désactivé (à éviter en prod) |

## 📚 Exercice 2 — Changer le mode SELinux

```yaml
- name: Passer en permissive (debug temporaire)
  ansible.posix.selinux:
    policy: targeted
    state: permissive
```

🔍 **Observation** : le module modifie `/etc/selinux/config` (effet **après
reboot**) ET applique le mode **maintenant** (`setenforce 0`).

**Désactiver complètement** (à éviter sauf cas spécial) :

```yaml
- ansible.posix.selinux:
    state: disabled
  notify: Reboot system
```

`state: disabled` **nécessite un reboot** pour prendre effet (le kernel doit
recharger la politique). Le module modifie `/etc/selinux/config` mais
**`getenforce`** continuera à afficher `Enforcing` jusqu'au reboot.

## 📚 Exercice 3 — Booléens SELinux

Les **booléens** SELinux sont des switches qui activent/désactivent des règles
de la politique. Ex : autoriser httpd à se connecter au réseau.

```yaml
- name: Lister les booleens HTTPD
  ansible.builtin.command: getsebool -a
  register: bools
  changed_when: false

- name: Filtrer ceux contenant "httpd"
  ansible.builtin.debug:
    msg: "{{ bools.stdout_lines | select('search', 'httpd') | list | first(5) }}"
```

🔍 **Observation** : sur RHEL 10, on a ~300 booléens. Les plus utiles RHCE :

| Booléen | Effet |
|---|---|
| `httpd_can_network_connect` | httpd peut faire des connexions sortantes |
| `httpd_can_network_connect_db` | httpd peut se connecter à une DB distante |
| `httpd_enable_homedirs` | httpd peut servir `~user/public_html/` |
| `nfs_export_all_rw` | NFS export en read-write |
| `samba_enable_home_dirs` | Samba peut partager les homes |

## 📚 Exercice 4 — Modifier un booléen avec persistance

```yaml
- name: Autoriser httpd a se connecter au reseau (persistant)
  ansible.posix.seboolean:
    name: httpd_can_network_connect
    state: true
    persistent: true
```

🔍 **Observation** :

- **Sans `persistent: true`** : changement uniquement **runtime** (perdu au
  reboot, équivalent `setsebool` simple).
- **Avec `persistent: true`** : changement **persisté** dans la politique
  (équivalent `setsebool -P`).

**Pour la production** : **toujours** `persistent: true`. Sans ça, après reboot
le service replante avec les mêmes erreurs SELinux.

## 📚 Exercice 5 — Contextes de fichiers (`sefcontext`)

Pattern fréquent : déployer une app web dans un dossier custom (pas
`/var/www/html/`). SELinux refuse à `httpd` de servir des fichiers qui n'ont
pas le bon **contexte SELinux**.

```yaml
- name: Definir le contexte httpd_sys_content_t pour /var/www/myapp
  community.general.sefcontext:
    target: '/var/www/myapp(/.*)?'
    setype: httpd_sys_content_t
    state: present

- name: Appliquer le contexte (restorecon)
  ansible.builtin.command: restorecon -Rv /var/www/myapp
  register: restorecon_result
  changed_when: "'relabeled' in restorecon_result.stdout"
```

🔍 **Observation** :

- **`sefcontext:`** ajoute la règle dans la politique (`semanage fcontext -a -t
  httpd_sys_content_t '/var/www/myapp(/.*)?'`).
- **`restorecon -R`** applique la règle aux fichiers existants (sinon ils
  gardent leur ancien contexte).

**Convention regex** : `(/.*)?` à la fin pour matcher le dossier ET tous ses
sous-éléments.

## 📚 Exercice 6 — Diagnostiquer une violation SELinux

```yaml
- name: Tenter d acceder a /var/www/myapp via httpd
  ansible.builtin.uri:
    url: http://localhost/myapp/
    status_code: [200, 403]   # On accepte 403 si SELinux bloque

- name: Verifier les violations dans audit.log
  ansible.builtin.command: |
    grep "denied" /var/log/audit/audit.log | tail -5
  register: denials
  changed_when: false
  failed_when: false
```

🔍 **Observation** : si SELinux bloque, `audit.log` contient des entries
`type=AVC msg=audit ... denied`. Outil **`audit2allow`** (paquet
`policycoreutils-python-utils`) génère un module SELinux qui autorise
exactement ce qui est bloqué :

```bash
ssh ansible@db1.lab 'sudo audit2allow -a -M myapp_local'
sudo semodule -i myapp_local.pp
```

**Mais** : ne **jamais** `audit2allow -a -M` aveuglément en prod — c'est
souvent une mauvaise idée. Préférer corriger le contexte (`sefcontext`) ou
activer un booléen.

## 📚 Exercice 7 — Le piège : SELinux désactivé pendant le développement

Pattern dangereux observé en prod :

```yaml
# ❌ Mauvaise pratique — desactive SELinux "pour que ca marche"
- ansible.posix.selinux:
    state: disabled
```

🔍 **Risques** :

- **Surface d'attaque augmentée** : SELinux est une couche de défense critique
  contre les exploits.
- **Audit échoué** : RHCE EX294, CIS Benchmark, ANSSI exigent SELinux activé.
- **Drift dev/prod** : le code marche en dev (SELinux off) mais plante en prod
  (SELinux on).

**Bonne pratique** : passer en `permissive` pour debug → identifier les
contextes/booléens manquants → corriger → revenir en `enforcing`.

## 🔍 Observations à noter

- **`ansible.posix.selinux:`** = état global (`enforcing`/`permissive`/`disabled`).
- **`ansible.posix.seboolean:`** = booléens — **toujours `persistent: true`** en prod.
- **`community.general.sefcontext:`** + **`restorecon -R`** = contextes de fichiers.
- **Changement vers `disabled`** nécessite un **reboot** pour prendre effet.
- **`policycoreutils-python-utils`** doit être installé sur le managed node.
- **Ne jamais désactiver SELinux** sauf cas critique documenté.

## 🤔 Questions de réflexion

1. Vous déployez une app dans `/opt/myapp/` qui doit être servie par httpd.
   `httpd` ne peut pas y accéder. Quel pipeline (booléen, sefcontext,
   restorecon) ?

2. Pourquoi `state: permissive` est-il **plus utile** que `state: disabled`
   pour le **debug** ? (indice : violations toujours loguées).

3. Vous voulez **lister tous les contextes** définis sur un dossier. Quelle
   commande shell + quel module Ansible ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`ansible.posix.seport:`** : associer un **port** à un type SELinux. Ex :
  faire tourner httpd sur 8080 (par défaut SELinux n'autorise httpd que sur
  80, 443, 8080, etc.).
- **`audit2allow -a`** : générer un **module SELinux custom** depuis les
  violations loguées. Outil de **dépannage** — pas de production aveugle.
- **Multi-policy** : RHEL 10 supporte `targeted` (par défaut) et `mls`
  (Multi-Level Security, secteur défense). Pas dans RHCE.
- **`semanage` CLI** : commande de référence pour explorer la politique
  (`semanage fcontext -l`, `semanage port -l`, `semanage boolean -l`).
- **Lab 44 (firewalld)** : compléter SELinux par les règles réseau pour une
  sécurité défense-en-profondeur.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-rhel/selinux/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-rhel/selinux/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-rhel/selinux/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
