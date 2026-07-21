# 🎯 Challenge — `authorized_key` multi-users avec restrictions

## ✅ Objectif

Sur **db1.lab**, provisionner **3 clés SSH** différentes :

1. Clé **personnelle d'alice** : libre (pas de restrictions).
2. Clé **personnelle de bob** : restreinte (`from="10.10.20.0/24"` + `no-pty`).
3. Clé **de service** dans le compte d'alice : commande forcée
   (`command="/usr/local/bin/backup.sh"`) + restrictions de session.

## 🧩 Le matériel de clés est déjà en place

`dsoxlab run` génère pour vous les paires de clés d'alice et de bob, sur le
control node, dans le répertoire `files/` du lab :

```text
labs/modules-utilisateurs/authorized-key/files/
├── alice.pub.key       # clé PRIVÉE (nom trompeur, conservé par compatibilité)
├── alice.pub.key.pub   # clé PUBLIQUE  <- c'est celle-ci que vous déployez
├── bob.pub.key
└── bob.pub.key.pub
```

Lisez bien les fichiers **`.pub.key.pub`** : `.pub.key` est la clé privée, malgré
son nom. Ces clés sont gitignorées, donc absentes d'un clone frais : c'est
précisément pour cela que le setup les crée.

> ⚠️ Ne les régénérez pas et ne les supprimez pas. Le commentaire porté par
> chaque clé (`alice@laptop`, `bob@laptop`) est vérifié par les tests pytest, et
> le setup ne régénère une paire que si sa clé privée manque : la supprimer vous
> donnerait une clé publique différente de celle déjà déployée.

## 🧩 Module à utiliser : `ansible.posix.authorized_key`

| Option | Effet |
| --- | --- |
| `user:` | Compte cible (`alice`, `bob`). |
| `key:` | La clé publique (string complète). |
| `state: present` | Ajoute si absent (idempotent). |
| `key_options:` | Préfixe la clé avec des options OpenSSH (`from=`, `command=`, `no-pty`, etc.). |

## 🧩 Squelette

```yaml
---
- name: Challenge - authorized_key multi-users
  hosts: db1.lab
  become: true

  vars:
    backup_service_key: "ssh-ed25519 AAAA<contenu_pubkey> backup@service"

  tasks:
    - name: Créer alice et bob
      ansible.builtin.user:
        name: ???
        state: present
        shell: /bin/bash
      loop: ???

    - name: Clé personnelle d'alice (libre)
      ansible.posix.authorized_key:
        user: ???
        key: "{{ lookup('file', ???) }}"
        state: present

    - name: Clé personnelle de bob (restreinte)
      ansible.posix.authorized_key:
        user: ???
        key: "{{ lookup('file', ???) }}"
        key_options: ???
        state: present

    - name: Clé de service backup pour alice (commande forcée)
      ansible.posix.authorized_key:
        user: ???
        key: ???
        key_options: ???
        state: present
```

> 💡 **`key_options:`** est une **chaîne** d'options séparées par virgules :
>
> ```text
> 'command="/usr/local/bin/backup.sh",no-pty,no-X11-forwarding,no-port-forwarding'
> ```
>
> Pour la clé de service, vous devez générer **votre propre clé publique
> ed25519 statique** (par ex avec `ssh-keygen -t ed25519 -N "" -C
> "backup@service"` pour obtenir la chaîne) et la coller dans `vars:`.

**Pièges** :

> - **`exclusive: true`** : remplace **toutes** les clés existantes par
>   celle fournie. Anti-pattern si vous voulez juste **ajouter** —
>   risque de bloquer l'accès en supprimant la clé du formateur.
> - **`key:`** = la clé publique **complète** (`ssh-ed25519 AAA…
>   user@host`). Pas seulement la partie base64.
> - **`state: present`** + clé déjà présente = idempotent, pas de
>   modification. Mais l'ordre des clés peut changer dans
>   `authorized_keys` — pas un bug.
> - **`manage_dir: true`** (défaut) : crée `~/.ssh/` avec les bonnes
>   permissions (0700). Sans, la clé peut être ignorée par sshd
>   (perms trop ouvertes).

## 🚀 Lancement

```bash
ansible-playbook labs/modules-utilisateurs/authorized-key/challenge/solution.yml
ansible db1.lab -b -m ansible.builtin.command -a "cat /home/alice/.ssh/authorized_keys"
ansible db1.lab -b -m ansible.builtin.command -a "cat /home/bob/.ssh/authorized_keys"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-utilisateurs/authorized-key/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-utilisateurs-authorized-key
```

## 💡 Pour aller plus loin

- **`exclusive: true`** : remplace **toutes** les clés du user par celle(s)
  fournie(s). Pratique pour purger des clés orphelines en un seul run.
- **`validate_certs:`** : sur `manage_dir: false`, ne touche pas à
  `~/.ssh/` (utile si géré par un autre outil).
- **Auditer les clés actives** : `ansible all -b -m ansible.builtin.shell -a
  "for u in $(getent passwd | cut -d: -f1); do echo == $u ==; cat
  /home/$u/.ssh/authorized_keys 2>/dev/null; done"`.
- **Lint** :

   ```bash
   ansible-lint labs/modules-utilisateurs/authorized-key/challenge/solution.yml
   ```
