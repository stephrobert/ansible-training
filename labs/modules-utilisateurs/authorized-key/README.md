# Lab 42 — Module `authorized_key:` (clés SSH des utilisateurs)

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

🔗 [**Module authorized_key Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-authorized-key/)

`ansible.posix.authorized_key:` gère les **clés SSH publiques** dans le fichier
`~/.ssh/authorized_keys` d'un utilisateur. C'est l'outil du **provisioning des
accès SSH** : ajouter, supprimer, ou **forcer la liste exclusive** des clés
autorisées.

Ce module appartient à la collection **`ansible.posix`** (pas builtin) — sur
Ansible Core 2.20, il faut `ansible-galaxy collection install ansible.posix`.

Options principales : **`user:`**, **`key:`**, **`state:`**, **`exclusive: true`**
(remplace toutes les clés existantes), **`comment:`**, **`key_options:`**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Ajouter** une clé SSH à un utilisateur existant.
2. **Distinguer** `state: present` (ajout) de `exclusive: true` (remplacement).
3. **Restreindre** une clé avec `key_options:` (`from=`, `command=`, `no-pty`).
4. **Charger** une clé depuis un fichier local (`lookup('file', ...)`).
5. **Provisionner** plusieurs clés pour plusieurs users en une seule passe avec
   `subelements`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible-galaxy collection install ansible.posix
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "for u in alice bob; do userdel -rf \$u 2>/dev/null; useradd \$u -m; done; true"
mkdir -p labs/modules-utilisateurs/authorized-key/files
```

Générez une clé SSH de test (locale) :

```bash
ssh-keygen -t ed25519 -f labs/modules-utilisateurs/authorized-key/files/alice.pub.key -N "" -C "alice@laptop"
ssh-keygen -t ed25519 -f labs/modules-utilisateurs/authorized-key/files/bob.pub.key -N "" -C "bob@laptop"
```

(On utilise `.pub.key` pour récupérer la **clé publique** sans les `_rsa`/`_ed25519`
qui pourraient être confondus avec un fichier de config SSH.)

## 📚 Exercice 1 — Ajouter une clé à un user

Créez `lab.yml` :

```yaml
---
- name: Demo authorized_key
  hosts: db1.lab
  become: true
  tasks:
    - name: Ajouter la cle d alice
      ansible.posix.authorized_key:
        user: alice
        key: "{{ lookup('file', 'files/alice.pub.key.pub') }}"
        state: present
```

**Lancez** :

```bash
ansible-playbook labs/modules-utilisateurs/authorized-key/lab.yml
ssh ansible@db1.lab 'sudo cat /home/alice/.ssh/authorized_keys'
```

🔍 **Observation** :

- 1er run : `changed=1` — création de `/home/alice/.ssh/` avec mode `0700` et de
  `authorized_keys` avec mode `0600` (Ansible respecte les permissions SSH
  strictes).
- 2ème run : `changed=0` — la clé est déjà présente.

**Lookup `file`** : Ansible **lit** le fichier local côté control node et
**injecte** son contenu en string. La clé n'est **pas transférée** comme un
fichier — c'est juste son contenu qui est ajouté à `authorized_keys`.

## 📚 Exercice 2 — `exclusive: true` (remplacement complet)

```yaml
- name: Pre-creer une cle "manuelle" dans authorized_keys
  ansible.builtin.lineinfile:
    path: /home/alice/.ssh/authorized_keys
    line: "ssh-rsa AAAAOLD-MANUAL-KEY old@laptop"
    create: true
    owner: alice
    group: alice
    mode: "0600"

- name: Forcer la liste exclusive (efface l ancienne cle)
  ansible.posix.authorized_key:
    user: alice
    key: "{{ lookup('file', 'files/alice.pub.key.pub') }}"
    state: present
    exclusive: true
```

**Vérifiez** :

```bash
ssh ansible@db1.lab 'sudo cat /home/alice/.ssh/authorized_keys'
```

🔍 **Observation** : seule la nouvelle clé est présente. **`exclusive: true`**
**efface** toutes les clés existantes pour ne laisser que celles spécifiées.

**Cas d'usage** : revoke d'accès massif (un développeur quitte l'équipe →
relancer le play sans sa clé pour la révoquer partout).

**Risque** : si `key:` est vide ou la lookup échoue, **toutes les clés sont
effacées**. À utiliser avec un `assert:` préalable.

## 📚 Exercice 3 — `key_options:` (restrictions de la clé)

```yaml
- name: Cle restreinte (from=IP + commande forcee)
  ansible.posix.authorized_key:
    user: bob
    key: "{{ lookup('file', 'files/bob.pub.key.pub') }}"
    state: present
    key_options: 'from="10.10.20.0/24",command="/usr/local/bin/restricted-cmd",no-pty,no-X11-forwarding'
```

🔍 **Observation** : la ligne dans `authorized_keys` est préfixée par les
restrictions :

```text
from="10.10.20.0/24",command="/usr/local/bin/restricted-cmd",no-pty,no-X11-forwarding ssh-ed25519 AAAA... bob@laptop
```

**Restrictions courantes** :

| Option | Effet |
|---|---|
| `from="IP_or_CIDR"` | Limite l'IP source autorisée |
| `command="/path"` | Force l'exécution de cette commande (ignore SSH command client) |
| `no-pty` | Pas de TTY (interdit `ssh user@host` interactif) |
| `no-X11-forwarding` | Pas de forwarding X11 |
| `no-port-forwarding` | Pas de tunnel SSH (`-L`, `-R`) |
| `no-agent-forwarding` | Pas de forwarding de l'agent SSH |

**Pattern security-hardened** : `from="" + command="" + no-pty + no-X11 + no-port`
pour des **clés de service** (rsync, backup, monitoring) — un attaquant qui vole
la clé ne peut **rien** faire d'autre que la commande imposée.

## 📚 Exercice 4 — Pattern multi-users avec `subelements`

```yaml
- name: Demo provisioning multi-users
  hosts: db1.lab
  become: true
  vars:
    team_users:
      - name: alice
        ssh_keys:
          - "ssh-ed25519 AAAA1 alice@laptop"
          - "ssh-ed25519 AAAA2 alice@server"
      - name: bob
        ssh_keys:
          - "ssh-ed25519 BBBB1 bob@laptop"
  tasks:
    - name: Ajouter chaque cle a chaque user (subelements)
      ansible.posix.authorized_key:
        user: "{{ item.0.name }}"
        key: "{{ item.1 }}"
        state: present
      loop: "{{ team_users | subelements('ssh_keys') }}"
      loop_control:
        label: "{{ item.0.name }} key {{ item.1[0:30] }}..."
```

🔍 **Observation** : `subelements` produit des paires `(parent, child)` —
parfait pour **N users avec M clés chacun**. Une seule tâche, idempotente.

Cf. lab 21 (with_subelements legacy) pour la migration depuis l'ancienne
syntaxe.

## 📚 Exercice 5 — Suppression d'une clé (`state: absent`)

```yaml
- name: Revoquer la cle d alice
  ansible.posix.authorized_key:
    user: alice
    key: "{{ lookup('file', 'files/alice.pub.key.pub') }}"
    state: absent
```

🔍 **Observation** : Ansible matche **par contenu de la clé** (pas par commentaire
ni par hash). Si vous générez une nouvelle clé, l'ancienne reste.

**Pattern revoke complet** : `state: absent` + `key: "{{ ancienne_clé }}"`. Si
vous avez plusieurs clés à révoquer, soit `loop:` sur les clés à enlever, soit
`exclusive: true` avec la liste finale.

## 📚 Exercice 6 — Charger les clés depuis un dossier (`*.pub`)

Pattern réel : tous les développeurs déposent leur clé publique dans
`files/users/<username>.pub`. Le playbook les charge automatiquement.

```yaml
- name: Recuperer la liste des fichiers .pub
  ansible.builtin.find:
    paths: "{{ inventory_dir }}/../files/users"
    patterns: '*.pub'
  delegate_to: localhost
  register: pub_keys

- name: Provisionner chaque user avec sa cle
  ansible.posix.authorized_key:
    user: "{{ item.path | basename | regex_replace('\\.pub$', '') }}"
    key: "{{ lookup('file', item.path) }}"
    state: present
  loop: "{{ pub_keys.files }}"
  loop_control:
    label: "{{ item.path | basename }}"
```

🔍 **Observation** : Ansible **dérive** le nom d'utilisateur depuis le nom de
fichier (`alice.pub` → user `alice`). Ajouter une nouvelle clé = juste déposer
`carl.pub` dans le dossier — pas besoin de modifier le playbook.

## 📚 Exercice 7 — Le piège : permissions SSH strictes

Si vous créez `~/.ssh/authorized_keys` **manuellement** (ou via `copy:`) avec
des permissions trop ouvertes, **SSH refuse** la clé.

```yaml
# ❌ Mauvais : pas de mode strict
- ansible.builtin.copy:
    content: "ssh-ed25519 AAAA... alice@laptop\n"
    dest: /home/alice/.ssh/authorized_keys
    owner: alice
    group: alice
    # Mode par defaut : 0644 → SSH REFUSE

# ✅ Bon
- ansible.builtin.copy:
    content: "ssh-ed25519 AAAA... alice@laptop\n"
    dest: /home/alice/.ssh/authorized_keys
    owner: alice
    group: alice
    mode: "0600"
```

🔍 **Observation** : `~/.ssh/` doit être **`0700`**, `~/.ssh/authorized_keys`
**`0600`**. Sinon `sshd` refuse en silence (logs `Authentication refused: bad
ownership or modes`). **`authorized_key:`** gère ça automatiquement — c'est une
des raisons de **préférer ce module à un `copy:` brut**.

## 🔍 Observations à noter

- **Module `ansible.posix.authorized_key:`** (pas builtin — collection requise).
- **`exclusive: true`** = remplace toutes les clés (utile pour révoque massive).
- **`key_options:`** = restrictions SSH (`from=`, `command=`, `no-pty`).
- **`lookup('file', ...)`** = charger la clé depuis un fichier local (control node).
- **Pattern `subelements`** = N users × M clés en une tâche.
- **`authorized_key:`** gère automatiquement les **permissions SSH strictes**
  (700/600).

## 🤔 Questions de réflexion

1. Vous voulez **revoke** la clé d'un développeur qui quitte l'équipe sur 100
   serveurs. Quel pattern : `state: absent` + clé exacte, ou `exclusive: true`
   avec la liste finale ? Avantages de chacun ?

2. Vous donnez une **clé de backup** à un script externe. Comment la limiter
   pour qu'elle puisse **uniquement** lancer `/usr/local/bin/backup.sh` ?
   (combinaison `key_options:`).

3. Vous avez 50 développeurs et 10 serveurs. Faut-il **`loop:` sur les users**
   ou **`loop:` sur les serveurs** ? (indice : `subelements` + `delegate_to`).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`manage_dir: false`** : ne pas créer `~/.ssh/` automatiquement. À utiliser
  si le home est sur NFS ou shared FS qui doit gérer ses propres permissions.
- **`path:`** : forcer un chemin custom au lieu de `~/.ssh/authorized_keys`.
  Pour des cas où SSH cherche les clés ailleurs (config sshd custom).
- **`validate_certs:`** : pour les clés depuis des URLs HTTPS — vérification
  TLS du serveur.
- **Pattern `git pull` + clé déployée** : la clé fournie par le module sert à
  un git pull automatisé. Combiner avec `key_options: command="git-shell -c"`.
- **Lab 43 (sudoers)** : compléter les clés SSH par les droits sudo.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/modules-utilisateurs/authorized-key/lab.yml

# Lint de votre solution challenge
ansible-lint labs/modules-utilisateurs/authorized-key/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/modules-utilisateurs/authorized-key/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
