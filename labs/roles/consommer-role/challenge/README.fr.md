# 🎯 Challenge — Consommer le rôle `webserver` des 3 façons, et le prouver

## ✅ Objectif

Écrire `challenge/solution.yml` : **3 plays** sur db1.lab qui consomment le
rôle `webserver` livré dans `roles/`, chacun par une forme différente
(`roles:`, `import_role`, `include_role`). Les tests ne lisent pas votre
YAML : ils vérifient **l'état de db1.lab**, y compris les traces qui
distinguent le statique (résolu au parsing) du dynamique (résolu au runtime).

Le rôle fournit deux entry points :

- `tasks/main.yml` : installe et configure nginx (le vrai déploiement) ;
- `tasks/stamp.yml` : pose `/tmp/consommer-{{ webserver_invocation }}.txt`,
  la trace de l'invocation. L'appelant fournit `webserver_invocation`.

## 🧩 Contrat attendu

### Play 1 — `roles:` (le déploiement systématique)

Consommer `webserver` au niveau du play, avec `webserver_listen_port: 8080`.

État vérifié sur db1 : paquet `nginx` installé, service **démarré et
activé**, nginx **écoute sur 8080**, page d'accueil par défaut du rôle
en place (mode `0644`).

### Play 2 — `import_role` (statique), gardé par un flag ÉTEINT

Dans un play avec `vars: {deploy_extras: false}` :

1. Importer (`ansible.builtin.import_role`) l'entry point `stamp.yml` avec
   `webserver_invocation: import`, gardé par `when: deploy_extras | bool`.
2. Puis une tâche qui écrit `/tmp/consommer-vars-import.txt` avec pour
   contenu `package={{ webserver_package | default('UNDEFINED') }}`,
   mode `0644`.

État vérifié : `/tmp/consommer-import.txt` **n'existe pas** (le `when:`
s'est appliqué à chaque tâche importée), MAIS
`/tmp/consommer-vars-import.txt` contient `package=nginx` : le rôle a été
**chargé au parsing**, ses defaults sont visibles dans le play, même si
aucune de ses tâches n'a tourné. C'est ça, « statique ».

### Play 3 — `include_role` (dynamique), sous condition runtime

1. Une tâche `ansible.builtin.service_facts:` : l'état réel des services,
   une information qui n'existe **qu'au runtime**.
2. Inclure (`ansible.builtin.include_role`) `stamp.yml` avec
   `webserver_invocation: include`, seulement si le service `nginx.service`
   est `running` dans `ansible_facts.services`.
3. Puis une tâche qui écrit `/tmp/consommer-vars-include.txt` avec le même
   contenu template que le play 2, mode `0644`.

État vérifié : `/tmp/consommer-include.txt` **existe** (la condition
runtime était vraie, le rôle a été chargé et exécuté à la volée), MAIS
`/tmp/consommer-vars-include.txt` contient `package=UNDEFINED` : un
`include_role` garde ses variables **privées** (sauf `public: true`).
Miroir exact du play 2 : exécuté mais invisible, contre visible mais
non exécuté.

## 🧩 Squelette

```yaml
---
- name: Play 1 - deploiement via roles
  hosts: ???
  become: true
  gather_facts: false
  roles:
    - role: ???
      vars:
        webserver_listen_port: ???

- name: Play 2 - import statique garde par un flag eteint
  hosts: ???
  become: true
  gather_facts: false
  vars:
    deploy_extras: false
  tasks:
    - name: Importer la trace (ne doit PAS s'executer)
      ansible.builtin.import_role:
        name: ???
        tasks_from: ???
      vars:
        webserver_invocation: ???
      when: ???

    - name: Tracer la visibilite des variables du role
      ansible.builtin.copy:
        dest: /tmp/consommer-vars-import.txt
        content: ???
        mode: "0644"

- name: Play 3 - include dynamique sous condition runtime
  hosts: ???
  become: true
  gather_facts: false
  tasks:
    - name: Etat des services (info qui n'existe qu'au runtime)
      ansible.builtin.service_facts:

    - name: Inclure la trace si nginx est actif
      ansible.builtin.include_role:
        name: ???
        tasks_from: ???
      vars:
        webserver_invocation: ???
      when: ???

    - name: Tracer la visibilite des variables du role
      ansible.builtin.copy:
        dest: /tmp/consommer-vars-include.txt
        content: ???
        mode: "0644"
```

> 💡 **Pièges** :
>
> - **`ANSIBLE_ROLES_PATH`** : le rôle vit dans `labs/roles/consommer-role/roles`,
>   pas à côté de `solution.yml`. Exportez
>   `ANSIBLE_ROLES_PATH=labs/roles/consommer-role/roles` avant de lancer
>   (pytest le fait pour vous).
> - **`tasks_from: stamp.yml`** : sans lui, `import_role`/`include_role`
>   rejouent `main.yml` et réinstallent nginx dans chaque play.
> - **`when:` sur un `import_role`** est recopié sur **chaque tâche** du
>   rôle : rien ne s'exécute, mais le rôle est déjà chargé. Sur un
>   `include_role`, le `when:` décide si le rôle est chargé **tout court**.
> - **Ne définissez `webserver_package` nulle part** dans votre playbook :
>   les deux fichiers `consommer-vars-*.txt` doivent révéler ce que chaque
>   forme expose réellement.

## 🚀 Lancement

```bash
ANSIBLE_ROLES_PATH=labs/roles/consommer-role/roles \
  ansible-playbook labs/roles/consommer-role/challenge/solution.yml
```

## 🧪 Validation

```bash
pytest -v labs/roles/consommer-role/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean roles-consommer-role
```

## 💡 Pour aller plus loin

- **Passez `deploy_extras: true`** (`-e deploy_extras=true`) : la trace
  `consommer-import.txt` apparaît. Le `when:` d'un import est bien évalué
  au runtime, tâche par tâche ; c'est le **chargement** qui est statique.
- **`public: true`** sur l'`include_role` : relancez et observez
  `consommer-vars-include.txt` passer à `package=nginx`.
- **`ansible-lint --profile production labs/roles/consommer-role/challenge/solution.yml`** :
  sortie attendue `Passed: 0 failure(s), 0 warning(s)`.
