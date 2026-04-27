# 🎯 Challenge — 3 groupes avec GIDs forcés + 1 groupe système

## ✅ Objectif

Sur **db1.lab**, créer 4 groupes via `ansible.builtin.group`, dont 3 avec
**GID explicite** (pour cohérence multi-hôtes) et 1 **système**
(GID < 1000 auto-attribué par le système).

## 🧩 Spécifications

| Nom | GID | Type |
| --- | --- | --- |
| `rhce-shared` | **4000** | standard, GID forcé |
| `rhce-admins` | **4001** | standard, GID forcé |
| `rhce-readonly` | **4002** | standard, GID forcé |
| `myapp-system` | (auto < 1000) | **système** |

> 💡 **Pourquoi forcer les GIDs ?** Sur un parc multi-hôtes (NFS, conteneurs
> partagés…), les permissions de fichiers sont stockées **par GID**, pas par
> nom de groupe. Si `rhce-shared` a GID 4000 sur un hôte et 1010 sur un
> autre, les ACL deviennent incohérentes.

## 🧩 Squelette

```yaml
---
- name: Challenge - 3 groupes RHCE + 1 système
  hosts: db1.lab
  become: true

  tasks:
    - name: Groupes RHCE avec GIDs forcés
      ansible.builtin.group:
        name: ???
        gid: ???
        state: present
      loop:
        - { name: rhce-shared, gid: 4000 }
        - { name: rhce-admins, gid: 4001 }
        - { name: rhce-readonly, gid: 4002 }
      loop_control:
        label: ???

    - name: Groupe système myapp-system (GID < 1000)
      ansible.builtin.group:
        name: ???
        system: ???
        state: present
```

> 💡 **Pièges** :
>
> - **`system: true`** crée un groupe avec GID < 1000 (range système).
>   Convention pour les groupes liés à des services/daemons.
> - **`gid:` explicite** : pour reproductibilité, fixer le GID. Sans,
>   `useradd` choisit le prochain disponible — peut varier entre VMs.
> - **`local: true`** : force la création dans `/etc/group` même si LDAP
>   est configuré comme NSS source. Sinon, le groupe peut "exister" via
>   LDAP mais pas localement.
> - **Suppression d'un groupe utilisé** : `state: absent` échoue si des
>   users ont ce groupe en primaire. Supprimer les users d'abord.

## 🚀 Lancement

```bash
ansible-playbook labs/modules-utilisateurs/group/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "getent group rhce-shared rhce-admins rhce-readonly myapp-system"
```

## 🧪 Validation automatisée

```bash
pytest -v labs/modules-utilisateurs/group/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/modules-utilisateurs/group clean
```

## 💡 Pour aller plus loin

- **GID conflict** : si vous lancez sur un hôte où GID 4000 est déjà pris par
  un autre groupe, la tâche échoue. Démontrez-le en posant manuellement un
  `groupadd -g 4000 autre-groupe` au préalable.
- **`local: true`** : crée le groupe en local (`/etc/group`) même si
  l'hôte utilise un système d'auth distant (LDAP, SSSD).
- **Lint** :

   ```bash
   ansible-lint labs/modules-utilisateurs/group/challenge/solution.yml
   ```
