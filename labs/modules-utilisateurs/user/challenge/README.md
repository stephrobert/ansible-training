# 🎯 Challenge — Provisionner 3 comptes RHCE

## ✅ Objectif

Sur **db1.lab**, créer 1 groupe + 3 comptes utilisateur avec des attributs
spécifiques à chacun.

## 🧩 Spécifications

### Groupe préalable

- `rhce-team` — groupe primaire des 3 users.

### Utilisateurs à créer

| Nom | Shell | Comment | Groupe primaire | Groupes secondaires | UID forcé | Home |
| --- | --- | --- | --- | --- | --- | --- |
| `alice` | `/bin/bash` | `Alice — admin` | `rhce-team` | `wheel` | (auto) | (défaut) |
| `bob` | `/bin/bash` | `Bob — dev` | `rhce-team` | — | **2001** | (défaut) |
| `deploy` | `/bin/bash` | `Compte applicatif deploy` | `rhce-team` | — | **2000** | `/opt/deploy/` |

## 🧩 Indices clés

- `ansible.builtin.user` est idempotent : un user déjà conforme → `ok` (pas
  changed).
- **`group:`** (singulier) = groupe primaire. **`groups:`** (pluriel) =
  liste de groupes secondaires.
- **`append: true`** sur `groups:` ajoute au lieu de **remplacer**. Sans ça,
  un user déjà membre d'autres groupes les **perdrait**.
- **`uid:`** force un UID. Si l'UID est déjà pris, la tâche échoue.
- **`create_home: true`** sur `deploy` (pour créer `/opt/deploy/`).

## 🧩 Squelette

```yaml
---
- name: Challenge - 3 comptes RHCE
  hosts: db1.lab
  become: true

  tasks:
    - name: Créer le groupe rhce-team
      ansible.builtin.group:
        name: ???
        state: present

    - name: Créer alice (admin avec sudo wheel)
      ansible.builtin.user:
        name: ???
        comment: ???
        shell: ???
        group: ???
        groups: ???
        append: ???
        state: present

    - name: Créer bob (dev avec UID forcé)
      ansible.builtin.user:
        name: ???
        comment: ???
        shell: ???
        uid: ???
        group: ???
        state: present

    - name: Créer deploy (compte applicatif)
      ansible.builtin.user:
        name: ???
        comment: ???
        shell: ???
        uid: ???
        home: ???
        create_home: ???
        group: ???
        state: present
```

> 💡 **Pièges** :
>
> - **UID conflit** : si l'UID est déjà pris (héritage d'un lab
>   précédent), `useradd` plante avec "UID is not unique". Le `make
>   clean` du lab amont doit nettoyer.
> - **`group:`** vs **`groups:`** : `group` = groupe primaire (un seul),
>   `groups` = groupes secondaires (liste). Confusion classique.
> - **`append: true`** avec `groups:` : ajoute aux groupes existants
>   sans les écraser. Sans, l'user perd ses anciens groupes !
> - **`password:`** doit être un **hash** (`crypt('motdepasse', 'sha512')`).
>   Pas la chaîne en clair. Pour un user sans password : `password: !`
>   (locked) ou `password: '*'`.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-utilisateurs/user/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "id alice bob deploy"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-utilisateurs/user/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-utilisateurs/user clean
```

## 💡 Pour aller plus loin

- **`generate_ssh_key: true`** : crée une paire de clés SSH dans
  `~/.ssh/` du user au moment de la création.
- **`password:`** : positionne un mot de passe (déjà hashé). Utilisez
  `password: "{{ 'monpassword' | password_hash('sha512') }}"`.
- **`expires:`** : timestamp Unix d'expiration du compte.
- **Lint** :

   ```bash
   ansible-lint labs/modules-utilisateurs/user/challenge/solution.yml
   ```
