# Lab 72 — Dépendances entre rôles (`meta/main.yml: dependencies:`)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis unique : les 4 VMs du lab répondent au ping.

## 🧠 Rappel

🔗 [**Dépendances entre rôles Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/dependencies/)

Un rôle peut **déclarer** d'autres rôles dont il dépend. Ansible les
exécute **avant** lui.

```yaml
# roles/webserver/meta/main.yml
dependencies:
  - role: selinux_setup
    vars:
      selinux_state: enforcing
  - role: firewall_setup
    vars:
      firewall_open_ports:
        - 80/tcp
        - 443/tcp
```

→ Quand on lance `webserver`, Ansible exécute **dans cet ordre** :
`selinux_setup` → `firewall_setup` → `webserver`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Déclarer des **`dependencies:`** dans `meta/main.yml`.
2. Passer des **variables** aux rôles dépendants.
3. Comprendre l'**ordre d'exécution** des dépendances.
4. Éviter le piège du **diamant** (A dépend de B et C, B et C
   dépendent de D — D s'exécute combien de fois ?).
5. Différencier `dependencies:` (méta) de `import_role`/`include_role`
   (lab 71).

## 🔧 Préparation

```bash
ansible db1.lab -m ansible.builtin.ping
```

## ⚙️ Arborescence

```text
labs/roles/dependencies/
├── README.md
├── Makefile
├── playbook.yml
└── roles/
    ├── webserver/
    │   ├── meta/main.yml         ← dependencies: [selinux_setup, firewall_setup]
    │   └── tasks/main.yml
    ├── selinux_setup/             ← rôle dépendance #1
    │   ├── meta/main.yml
    │   ├── tasks/main.yml
    │   └── defaults/main.yml
    └── firewall_setup/            ← rôle dépendance #2
        ├── meta/main.yml
        ├── tasks/main.yml
        └── defaults/main.yml
```

## 📚 Exercice 1 — Lire `roles/webserver/meta/main.yml`

```yaml
galaxy_info:
  # ... (champs du lab 60) ...

dependencies:
  - role: selinux_setup
    vars:
      selinux_state: enforcing
      selinux_booleans:
        - httpd_can_network_connect

  - role: firewall_setup
    vars:
      firewall_open_ports:
        - 80/tcp
        - 443/tcp
```

🔍 **Observation** :

- **2 dépendances** déclarées avec leurs vars.
- **Ordre d'exécution** : `selinux_setup` → `firewall_setup` → `webserver`.
- Les **vars passées** sont scoped à la dépendance (ne polluent pas le
  rôle parent).

## 📚 Exercice 2 — Rôle dépendance `selinux_setup`

```yaml
# roles/selinux_setup/tasks/main.yml
- name: Vérifier que SELinux est en {{ selinux_state }}
  ansible.posix.selinux:
    policy: targeted
    state: "{{ selinux_state }}"

- name: Activer les booléens SELinux
  ansible.posix.seboolean:
    name: "{{ item }}"
    state: true
    persistent: true
  loop: "{{ selinux_booleans }}"
```

🔍 **Observation** : un rôle "dépendance" a **exactement** la même
structure qu'un rôle normal. La seule différence : il est référencé
par d'autres dans `meta/main.yml`.

## 📚 Exercice 3 — Lancer le play

```bash
ansible-playbook labs/roles/dependencies/playbook.yml
```

🔍 **Sortie attendue** :

```text
TASK [selinux_setup : Vérifier que SELinux est en enforcing]
TASK [selinux_setup : Activer les booléens SELinux]
TASK [firewall_setup : Installer firewalld]
TASK [firewall_setup : Ouvrir les ports 80, 443]
TASK [webserver : Installer nginx]
TASK [webserver : ...]
```

Les dépendances sont exécutées **en premier** (dans l'ordre de
déclaration), puis le rôle.

## 📚 Exercice 4 — Le piège du diamant

```text
       myapp
         │
    ┌────┴────┐
    ▼         ▼
selinux    firewall
    │         │
    └────┬────┘
         ▼
       common
```

Si `selinux_setup` et `firewall_setup` dépendent tous deux de `common`,
**combien de fois `common` tourne-t-il** ?

**Réponse** : **une seule fois**. Ansible déduplique les dépendances
identiques (même nom + mêmes vars).

> ⚠️ **Mais attention** : si `selinux_setup` appelle `common` avec
> `vars: {x: 1}` et `firewall_setup` avec `vars: {x: 2}`, alors `common`
> tourne **2 fois** (vars différentes = considéré comme différent).

## 📚 Exercice 5 — `dependencies:` vs `include_role:`

| Aspect | `dependencies:` (meta) | `include_role:` (tasks) |
| --- | --- | --- |
| Lieu de déclaration | `meta/main.yml` | `tasks/main.yml` |
| Évaluation | Statique (au parsing) | Dynamique (runtime) |
| Conditionnel | Non (sauf via `when:` propagé) | Oui (`when:` au runtime) |
| Visible dans `--list-tasks` | Non (pas explicitement) | Oui |
| Cas d'usage | Pré-requis structurel **toujours** appliqué | Choix runtime selon variable |

## 🔍 Observations à noter

- **`dependencies:`** garantit qu'un rôle a ses **pré-requis structurels**
  satisfaits, **avant** sa propre exécution.
- Les **vars passées aux dépendances** sont scoped — ne polluent pas
  le rôle parent.
- **Déduplication automatique** des dépendances identiques (sauf si
  vars différentes).
- **Pattern common** : un rôle `common` (utilisateurs base, paquets de
  base) dont presque tout le reste dépend.

## 🤔 Questions de réflexion

1. Vous voulez que `selinux_setup` ne tourne **que sur RHEL** (pas
   Debian). Comment l'exprimer dans `dependencies:` ? (Indice :
   `when:` propagé.)

2. Vous avez un rôle `common` qui pose des fichiers, et 3 rôles qui
   en dépendent. Sur un play qui appelle les 3 rôles, combien de fois
   `common` tourne-t-il ?

3. Quand préférer `dependencies:` à `include_role: + when:` ? Donnez
   un cas où l'un est meilleur que l'autre.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`allow_duplicates: true`** sur le rôle dépendance : l'autorise à
  s'exécuter plusieurs fois (par défaut, une seule).
- **`role_path`** : où Ansible cherche les rôles (priorités :
  `roles/`, `~/.ansible/roles/`, `/usr/share/ansible/roles/`).
- **Anti-pattern** : ne pas chaîner `dependencies:` sur 5 niveaux de
  profondeur. Plus lisible : un play parent qui orchestre.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/roles/dependencies/
```
