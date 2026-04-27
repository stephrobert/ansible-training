# Lab 71 — Consommer un rôle : `roles:`, `import_role`, `include_role`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Pré-requis unique : les 4 VMs du lab répondent au ping (cf. [README racine](../../README.md#-démarrage-rapide)).

## 🧠 Rappel

🔗 [**Consommer un rôle Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/consommer-role/)

Il existe **3 façons** d'utiliser un rôle dans un play. Choisir la bonne
selon le besoin :

| Forme | Quand l'utiliser | Évaluation |
| --- | --- | --- |
| **`roles:`** au niveau play | Cas standard, rôle systématique | Statique |
| **`import_role:`** dans `tasks:` | Rôle conditionnel sur tag, mais évalué au parsing | Statique (tags/when résolus tôt) |
| **`include_role:`** dans `tasks:` | Rôle conditionnel sur variable runtime, ou loop sur N rôles | Dynamique (when évalué au runtime) |

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Utiliser **`roles:`** au niveau play (forme standard).
2. Utiliser **`import_role:`** dans `tasks:` (statique).
3. Utiliser **`include_role:`** avec **`when:`** (dynamique).
4. Choisir la bonne forme selon le besoin (statique vs dynamique).
5. Comprendre pourquoi `import_role + when` ne se comporte **pas** comme
   `include_role + when`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ansible.builtin.ping
```

## ⚙️ Arborescence

```text
labs/roles/consommer-role/
├── README.md
├── Makefile
├── playbook.yml          ← démontre les 3 formes
└── roles/
    └── webserver/
```

## 📚 Exercice 1 — Forme `roles:` (la plus simple)

```yaml
---
- name: Forme classique avec roles:
  hosts: db1.lab
  become: true

  roles:
    - role: webserver
      vars:
        webserver_listen_port: 8080
```

🔍 **Observation** :

- Tourne **toujours** (pas de conditionnel possible au niveau play).
- Tourne **avant** `tasks:` du play (`pre_tasks` < `roles:` < `tasks:` < `post_tasks:`).
- Variables passées via `vars:` du rôle.

## 📚 Exercice 2 — `import_role:` (statique)

```yaml
- name: Avec import_role
  hosts: db1.lab
  become: true

  tasks:
    - name: Pre-task
      ansible.builtin.debug:
        msg: "avant le rôle"

    - name: Importer le rôle webserver
      ansible.builtin.import_role:
        name: webserver
      vars:
        webserver_listen_port: 8081
```

🔍 **Observation** :

- Permet de **placer** le rôle au milieu de tâches (pas seulement avant).
- **Statique** : les tâches du rôle sont expansées au **parsing**. Un
  `tags:` posé au-dessus s'applique à toutes les tâches du rôle. Un
  `when:` pareil mais **évalué pour chaque tâche** (pas globalement).

## 📚 Exercice 3 — `include_role:` (dynamique)

```yaml
- name: Avec include_role conditionnel
  hosts: db1.lab
  become: true
  vars:
    deploy_webserver: true

  tasks:
    - name: Inclure le rôle webserver SI deploy_webserver=true
      ansible.builtin.include_role:
        name: webserver
      vars:
        webserver_listen_port: 8082
      when: deploy_webserver | bool
```

🔍 **Observation** :

- **Dynamique** : le rôle n'est chargé **que si** `when:` est vrai au
  runtime.
- Permet de **boucler** sur une liste de rôles : `loop: [r1, r2, r3]` avec
  `include_role: name: "{{ item }}"`.
- Plus lourd à l'exécution que `import_role` (chargement à la volée).

## 📚 Exercice 4 — Comparer les comportements

Lancez :

```bash
ansible-playbook labs/roles/consommer-role/playbook.yml
```

🔍 **Observation** :

- Au **parsing**, `roles:` et `import_role:` sont déjà expansés. Vous
  voyez les noms des tâches du rôle dans `--list-tasks`.
- `include_role:` n'apparaît **pas** dans `--list-tasks` : son contenu
  est invisible jusqu'au runtime.

## 🔍 Observations à noter

- **`roles:`** = défaut, le plus simple. Utilisez-le.
- **`import_role:`** quand vous voulez **placer** le rôle au milieu de
  tâches.
- **`include_role:`** quand le rôle doit être **conditionnel runtime**
  (variable extra-vars) ou **loop**.
- **Piège `import_role + when:`** : le `when:` s'applique à **chaque
  tâche** du rôle individuellement, pas globalement. Pour ne pas
  charger le rôle du tout : `include_role + when:`.

## 🤔 Questions de réflexion

1. Vous avez 3 rôles `webserver`, `database`, `cache`. Vous voulez
   exécuter celui correspondant à `var: app_role`. Quelle forme
   utiliser ? Pourquoi pas `roles:` ?

2. Vous avez un rôle `firewall` que vous voulez tagger `firewall` pour
   pouvoir filtrer avec `--tags firewall`. `roles:` ou `import_role:` ?

3. Quel est le problème avec ce code ? :

   ```yaml
   - import_role:
       name: webserver
     when: ansible_os_family == "RedHat"
   ```

   Spoiler : sur Debian, le `when:` est évalué **par tâche** du rôle, donc
   chaque tâche est `skipped` — mais le rôle est quand même **chargé**,
   ce qui peut planter sur des `include_vars` qui n'ont pas le
   `Debian.yml`. Solution : `include_role + when:`.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md).

## 💡 Pour aller plus loin

- **`tasks_from:`** sur `import_role`/`include_role` : appeler un
  entry point alternatif du rôle (ex : `tasks/configure.yml` au lieu
  de `tasks/main.yml`).
- **`apply:`** sur `include_role` : forcer des `tags:` ou un `become:`
  sur l'inclusion.
- **`public: true`** sur `include_role` : rendre les variables du rôle
  visibles après inclusion (par défaut elles sont privées).

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/roles/consommer-role/playbook.yml
```
