# Lab 59 — Variables `defaults/` vs `vars/` dans un rôle

> 💡 **Pré-requis** : 4 VMs du lab répondent au ping Ansible.
>
> ```bash
> ansible all -m ansible.builtin.ping
> ```

## 🧠 Rappel

🔗 [**Variables defaults vs vars**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/variables-defaults-vars/)

Un rôle Ansible expose des **variables d'entrée** que l'utilisateur peut paramétrer. Deux dossiers pour ça :

- **`defaults/`** : valeurs par défaut, **override-ables**. Priorité **2** sur 22 dans la précédence Ansible (très basse).
- **`vars/`** : constantes internes, **NON override-ables**. Priorité **18** sur 22 (très haute).

**Règle simple** : si l'utilisateur DOIT pouvoir changer la valeur, c'est dans `defaults/`. Si la valeur est un détail interne (chemin système, mapping OS), c'est dans `vars/`.

Ce lab étend le rôle `webserver` du **lab 58** pour démontrer cette distinction et la **précédence**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Distinguer **`defaults/main.yml`** (override-ables) de **`vars/main.yml`** (internes).
2. Brancher des **variables aux tâches** via `{{ var_name }}`.
3. Override les variables depuis un **playbook** avec `vars:`.
4. Comprendre la **précédence** : `defaults/` < `vars: du play` < `vars/`.
5. Utiliser les variables dans un **template Jinja2** (`nginx.conf.j2`).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/roles/variables-defaults-vars
```

## ⚙️ Arborescence cible

```text
labs/roles/variables-defaults-vars/
├── README.md
├── playbook.yml          ← démo : utilise les valeurs DEFAULT
├── roles/
│   └── webserver/
│       ├── tasks/main.yml
│       ├── defaults/main.yml    ← override-ables
│       ├── vars/main.yml        ← internes
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       ├── templates/
│       │   └── nginx.conf.j2    ← template qui CONSOMME les variables
│       └── README.md
└── challenge/
    ├── README.md
    ├── solution.yml      ← override : webserver_listen_port: 8080
    ├── roles/            ← symlink vers ../roles
    └── tests/
        └── test_variables.py
```

## 📚 Exercice 1 — Lire `defaults/main.yml`

```bash
cat roles/webserver/defaults/main.yml
```

8 variables avec valeurs par défaut. Toutes préfixées par **`webserver_`** (convention nom du rôle pour éviter les collisions).

🔍 **Observation** : ces 8 variables sont **publiques** — l'utilisateur du rôle peut toutes les redéfinir dans son playbook ou ses `group_vars/`.

## 📚 Exercice 2 — Lire `vars/main.yml`

```bash
cat roles/webserver/vars/main.yml
```

4 variables avec **double underscore** (`__webserver_config_dir`, etc.). Convention pour signaler **« usage interne, ne pas modifier »**.

🔍 **Observation** : ces 4 variables sont des **chemins système** qui ne dépendent pas du choix de l'utilisateur. Si elles étaient dans `defaults/`, un utilisateur pourrait casser le rôle en redéfinissant `__webserver_html_dir`.

## 📚 Exercice 3 — Lire le template `nginx.conf.j2`

```bash
cat roles/webserver/templates/nginx.conf.j2
```

Le template consomme **5 variables** différentes :

- `{{ webserver_worker_processes }}` (defaults/)
- `{{ webserver_worker_connections }}` (defaults/)
- `{{ webserver_listen_port }}` (defaults/)
- `{{ __webserver_log_dir }}` (vars/)
- `{{ __webserver_html_dir }}` (vars/)

🔍 **Observation** : le template utilise **indistinctement** des variables de `defaults/` et `vars/`. Pour Jinja, ce sont juste des variables — la distinction de précédence se passe en amont quand Ansible résout les valeurs.

## 📚 Exercice 4 — Lancer avec les valeurs PAR DÉFAUT

```bash
ansible-playbook playbook.yml
```

Le playbook **n'override aucune variable**. Le rôle s'exécute avec :

- `webserver_listen_port: 80` (défaut de `defaults/main.yml`)
- `webserver_index_content: "<h1>Hello from web1.lab</h1>"` (défaut)

🔍 **Observation** : sur web1, nginx écoute sur **80**. Tester :

```bash
curl http://web1.lab/
# → <h1>Hello from web1.lab</h1>
```

## 📚 Exercice 5 — Override depuis le playbook

Maintenant, créer un playbook qui **override** certaines variables :

```yaml
---
- name: Webserver avec port custom
  hosts: web1.lab
  become: true
  roles:
    - role: webserver
      vars:
        webserver_listen_port: 9090
        webserver_index_content: "Custom message override"
```

Lancer ce playbook (en remplaçant temporairement `playbook.yml`). Maintenant nginx écoute sur **9090** au lieu de 80.

🔍 **Observation** : les `vars:` du **play** ont **gagné** sur les valeurs de `defaults/main.yml`. C'est la précédence en action.

## 📚 Exercice 6 — Tenter d'override `__webserver_html_dir` (variable de `vars/`)

Tentez ce playbook :

```yaml
- name: Tenter override d'une vars/ interne
  hosts: web1.lab
  become: true
  roles:
    - role: webserver
      vars:
        __webserver_html_dir: /tmp/test    # ← variable interne de vars/
```

Lancez et observez : la **valeur d'override n'est PAS appliquée**. La page d'accueil reste dans `/usr/share/nginx/html/`. Pourquoi ?

🔍 **Observation cruciale** : `vars/main.yml` du rôle a **priorité 18** sur 22. Le `vars:` du play a **priorité 13**. Donc `vars/` du rôle **gagne**, l'override est ignoré.

C'est exactement pourquoi on met les **constantes internes** dans `vars/` : on **protège** le rôle contre des modifications accidentelles par l'utilisateur.

## 📚 Exercice 7 — Override avec `--extra-vars` (priorité 22, le top)

```bash
ansible-playbook playbook.yml \
  --extra-vars "webserver_listen_port=12345"
```

`--extra-vars` est **priorité 22**, au-dessus de tout. Cette fois, nginx écoute sur 12345.

🔍 **Observation** : `--extra-vars` peut override **TOUT**, même les `vars/main.yml` du rôle :

```bash
ansible-playbook playbook.yml \
  --extra-vars "__webserver_html_dir=/tmp/extra"
```

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Dans quel cas mettre une variable dans `vars/` plutôt que `defaults/` ?

2. Pourquoi préfixer les variables avec le nom du rôle (`webserver_listen_port`) ?

3. Si une même variable est définie dans `host_vars/web1.lab.yml` ET dans `vars:` du play, qui gagne ?

4. Comment **tester l'effet** d'un changement de variable sans relancer le déploiement complet ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande d'**override 3 variables** dans un playbook qui cible `db1.lab` :

- `webserver_listen_port: 8080`
- `webserver_worker_connections: 2048`
- `webserver_index_content: "Custom page from challenge lab 59 on {{ inventory_hostname }}"`

Tests automatisés via `pytest+testinfra` (5 tests) :

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Lire la précédence officielle** : 22 niveaux documentés [ici](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence).
- **Pattern dossier** pour `defaults/` : sur des rôles complexes, splitter en plusieurs fichiers (`defaults/main.yml`, `defaults/network.yml`, `defaults/security.yml`).
- **`vars/` distrib-spécifique** : `vars/RedHat.yml`, `vars/Debian.yml` chargés dynamiquement via `include_vars: "{{ ansible_os_family }}.yml"` — pattern courant pour les rôles multi-distros.
- **Le lab 60** ajoutera des **handlers** au rôle — actions réactives déclenchées par `notify:`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/roles/variables-defaults-vars/lab.yml
ansible-lint labs/roles/variables-defaults-vars/challenge/solution.yml
ansible-lint --profile production labs/roles/variables-defaults-vars/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
