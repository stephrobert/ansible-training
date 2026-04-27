# Lab 51 — Module `stat:` (info sur fichiers et dossiers)

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

🔗 [**Module stat Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-stat/)

`ansible.builtin.stat:` retourne des **informations** sur un fichier ou dossier
sans le modifier : existence, type, taille, mode, owner, checksum, mtime.
C'est **le module n°1 de la logique conditionnelle** Ansible — combiné avec
`register:` + `when:`, il permet de coder des branches sûres.

`stat:` est **lecture seule** par définition — toujours `changed=0`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Vérifier l'existence** d'un fichier avant d'agir dessus.
2. **Distinguer** les types : fichier régulier, dossier, symlink, hardlink.
3. **Comparer des checksums** pour détecter une modification (`get_checksum: true`).
4. **Mesurer** la taille et le mtime pour des contrôles de conformité.
5. **Diagnostiquer** un fichier symlink qui pointe vers le vide.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/lab-stat-*"
```

## 📚 Exercice 1 — Existence d'un fichier

Créez `lab.yml` :

```yaml
---
- name: Demo stat
  hosts: db1.lab
  become: true
  tasks:
    - name: Stat sur /etc/passwd
      ansible.builtin.stat:
        path: /etc/passwd
      register: passwd_stat

    - name: Inspecter le resultat
      ansible.builtin.debug:
        var: passwd_stat.stat
```

🔍 **Observation** : `passwd_stat.stat` est un dict qui contient :

```yaml
exists: true
isfile: true
isdir: false
islnk: false
size: 1234
mode: '0644'
uid: 0
gid: 0
pw_name: root
gr_name: root
mtime: 1234567890
checksum: <SHA1 du contenu>
```

Note : sur des dossiers, `isdir: true`. Sur des symlinks, `islnk: true` + `lnk_source` pointe vers la cible.

## 📚 Exercice 2 — Conditionner sur l'existence (`when:`)

```yaml
- name: Stat sur un fichier optionnel
  ansible.builtin.stat:
    path: /etc/myapp.conf
  register: myapp_conf

- name: Action SI le fichier existe
  ansible.builtin.copy:
    src: /etc/myapp.conf
    dest: /tmp/lab-stat-backup.conf
    remote_src: true
  when: myapp_conf.stat.exists

- name: Action SI le fichier n existe PAS
  ansible.builtin.copy:
    content: "Default config\n"
    dest: /etc/myapp.conf
    mode: "0644"
  when: not myapp_conf.stat.exists
```

🔍 **Observation** : pattern **branche conditionnelle** classique. Avant
toute opération sur un fichier qui peut ou non exister, on stat puis on
décide.

## 📚 Exercice 3 — Distinguer les types

```yaml
- name: Stat sur un dossier
  ansible.builtin.stat:
    path: /etc
  register: etc_stat

- name: Stat sur un symlink (etc/localtime souvent)
  ansible.builtin.stat:
    path: /etc/localtime
  register: localtime_stat

- name: Afficher les types
  ansible.builtin.debug:
    msg: |
      /etc        → exists: {{ etc_stat.stat.exists }}, isdir: {{ etc_stat.stat.isdir }}
      /etc/localtime → exists: {{ localtime_stat.stat.exists }}, islnk: {{ localtime_stat.stat.islnk }}, target: {{ localtime_stat.stat.lnk_source | default('N/A') }}
```

🔍 **Observation** : champs disponibles selon le type :

| Type | Champs distinctifs |
|---|---|
| Fichier régulier | `isfile: true`, `size`, `checksum` |
| Dossier | `isdir: true` (pas de `size` significatif) |
| Symlink | `islnk: true`, `lnk_source` (cible), `lnk_target` (chemin résolu) |
| Hardlink | `nlink > 1` (nombre de liens) |
| Block/char device | `isblk: true` / `ischr: true` |

## 📚 Exercice 4 — Checksum pour détection de modification

```yaml
- name: Stat avec checksum
  ansible.builtin.stat:
    path: /etc/passwd
    get_checksum: true
    checksum_algorithm: sha256
  register: passwd_check

- name: Afficher le checksum
  ansible.builtin.debug:
    msg: "SHA256 de /etc/passwd : {{ passwd_check.stat.checksum }}"
```

**Attention performance** : `get_checksum: true` calcule le hash en lisant
tout le fichier. Sur un fichier de 1Go, c'est lent. À utiliser uniquement
quand vous **avez besoin** du checksum (audit, idempotence custom).

**Algorithmes supportés** : `sha1` (défaut), `sha256` (recommandé), `sha512`,
`md5` (déprécié).

## 📚 Exercice 5 — Mtime et tests temporels

```yaml
- name: Stat avec mtime
  ansible.builtin.stat:
    path: /etc/passwd
  register: passwd_mtime

- name: Verifier que /etc/passwd n a pas ete modifie depuis 24h
  ansible.builtin.assert:
    that:
      - (ansible_date_time.epoch | int - passwd_mtime.stat.mtime | int) < 86400
    fail_msg: "ALERTE : /etc/passwd modifie depuis moins de 24h"
    success_msg: "OK : /etc/passwd stable depuis 24h+"
```

🔍 **Observation** : `mtime` est un **timestamp Unix** (secondes depuis
1970). Pour comparer, soustraire et comparer en secondes.

**Cas d'usage** : audit de sécurité — détecter les modifs récentes sur
des fichiers sensibles.

## 📚 Exercice 6 — Le piège : symlink cassé

```yaml
- name: Creer un symlink vers une cible inexistante
  ansible.builtin.file:
    src: /opt/non-existent
    dest: /tmp/lab-stat-broken-link
    state: link
    force: true

- name: Stat sur le symlink (ne suit PAS le lien par defaut)
  ansible.builtin.stat:
    path: /tmp/lab-stat-broken-link
  register: link_stat

- name: Afficher (le symlink existe mais sa cible n existe pas)
  ansible.builtin.debug:
    msg: |
      exists: {{ link_stat.stat.exists }}
      islnk: {{ link_stat.stat.islnk }}
      lnk_source: {{ link_stat.stat.lnk_source | default('N/A') }}
```

🔍 **Observation** : par défaut, `stat:` ne **suit pas** les symlinks
(`follow: false`). Le symlink lui-même existe (`exists: true`), mais sa
cible peut être absente.

**Pour suivre le lien** :

```yaml
- ansible.builtin.stat:
    path: /tmp/lab-stat-broken-link
    follow: true
  register: link_stat_follow
  failed_when: false   # follow + cible absente = erreur sinon
```

Avec `follow: true`, `exists: false` si la cible n'existe pas.

## 📚 Exercice 7 — Diff de checksum entre deux fichiers

```yaml
- name: Stat sur le fichier source
  ansible.builtin.stat:
    path: /etc/hosts
    get_checksum: true
  register: src_stat

- name: Stat sur le fichier cible
  ansible.builtin.stat:
    path: /tmp/lab-stat-hosts-copy
    get_checksum: true
  register: dst_stat

- name: Comparer
  ansible.builtin.debug:
    msg: |
      Src checksum : {{ src_stat.stat.checksum }}
      Dst exists : {{ dst_stat.stat.exists }}
      {% if dst_stat.stat.exists %}
      Dst checksum : {{ dst_stat.stat.checksum }}
      Identique : {{ src_stat.stat.checksum == dst_stat.stat.checksum }}
      {% endif %}
```

Pattern utile pour **valider** un transfert ou détecter une **dérive** entre
deux fichiers — sans utiliser de `command: diff`.

## 🔍 Observations à noter

- **`stat:`** = lecture seule, toujours `changed=0`.
- **`register:` puis `when: var.stat.exists`** = pattern de logique
  conditionnelle de base.
- **`isfile`, `isdir`, `islnk`** = distinction des types.
- **`get_checksum: true`** = nécessite la lecture complète du fichier (lent
  sur gros fichiers).
- **`follow: false`** (défaut) = stat sur le symlink lui-même, pas sur la
  cible.
- **`mtime`** = timestamp Unix, comparer à `ansible_date_time.epoch`.

## 🤔 Questions de réflexion

1. Vous voulez **copier un fichier seulement s'il n'a pas été modifié**
   localement par l'utilisateur. Quelle combinaison `stat: + checksum +
   when:` ?

2. Différence sémantique entre `stat: follow: true` et `stat: follow:
   false` — quand préférer chaque ?

3. Vous voulez auditer **tous les binaires setuid** dans `/usr/bin/`. Faut-il
   `stat:` (avec quoi ?) ou `find:` (lab 52) ? Pourquoi ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`get_md5: false`** (défaut depuis Ansible 2.x) : MD5 est déprécié.
  Toujours utiliser `sha256`.
- **`get_attributes: false`** (défaut) : permet de récupérer les attributs
  étendus (xattr) — coûteux mais utile pour audit SELinux.
- **`get_mime: false`** (défaut) : MIME-type via `file -i`. Pratique pour
  des audits de contenu.
- **Lab 52 (`find:`)** : pour des recherches **multi-fichiers** par
  pattern, le module `stat:` ne suffit pas (il prend un `path:` unique).
- **Lab 53 (`assert:`)** : combiner `stat:` + `assert:` pour des
  validations défensives en début de play.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/modules-diagnostic/stat/lab.yml
ansible-lint labs/modules-diagnostic/stat/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/stat/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
