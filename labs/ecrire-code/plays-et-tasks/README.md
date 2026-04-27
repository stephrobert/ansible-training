# Lab 05 — Plays et tasks (anatomie complète d'un play)

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

🔗 [**Plays et tasks Ansible : anatomie complète, ordre d'exécution, mots-clés**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/plays-et-tasks/)

Au lab 04, vous avez écrit un play simple avec juste `tasks:`. Mais un vrai play en production a **4 sections de tâches** qui s'exécutent dans un ordre précis :

```text
gather_facts → pre_tasks → roles → tasks → post_tasks → handlers
```

Chaque section a son rôle :

- **`pre_tasks`** : préparatifs (snapshot, drainer un load balancer, poser un marqueur de début).
- **`roles`** : code factorisé et réutilisable (vu plus tard).
- **`tasks`** : le cœur du déploiement.
- **`post_tasks`** : vérifications post-déploiement (smoke test, marqueur de fin, notification).
- **`handlers`** : tâches **réactives**, déclenchées uniquement si une autre tâche `notify:` (lab 06).

> Les mots-clés de **parallélisme** (`serial:`, `strategy:`, `max_fail_percentage:`) ne sont **pas** abordés ici — ils sont l'objet du [lab 09 — parallélisme et stratégies](../09-ecrire-code-parallelisme-strategies/). Concentrez-vous d'abord sur l'**anatomie d'un play**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un play structuré avec **`pre_tasks` + `tasks` + `post_tasks` + `handlers`**.
2. Vérifier l'**ordre d'exécution** réel via des fichiers marqueurs horodatés.
3. Distinguer un handler d'une tâche normale.
4. Comprendre comment `notify:` déclenche un handler — et pourquoi un handler `ok` ne tourne pas.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible webservers -m ansible.builtin.ping
ansible webservers -b -m ansible.builtin.shell -a "rm -f /tmp/predeploy-* /tmp/postdeploy-*"
```

Réponse attendue : 2 `pong`, puis nettoyage des marqueurs d'un éventuel run précédent.

## ⚙️ Arborescence cible

```text
labs/ecrire-code/plays-et-tasks/
├── README.md           ← ce fichier
├── playbook.yml        ← À CRÉER — votre play complet
└── challenge/
    ├── README.md       ← challenge final (déjà présent)
    └── tests/
        └── test_*.py   ← (déjà présent — pytest+testinfra)
```

## 📚 Exercice 1 — Squelette du play

Créez `labs/ecrire-code/plays-et-tasks/playbook.yml` :

```yaml
---
- name: Déployer nginx avec play complet (pre/tasks/post/handlers)
  hosts: webservers
  become: true

  pre_tasks:
    # Vous allez écrire ici : poser un fichier marqueur "predeploy"

  tasks:
    # Vous allez écrire ici : installer + démarrer + configurer nginx

  post_tasks:
    # Vous allez écrire ici : poser un fichier marqueur "postdeploy"

  handlers:
    # Vous allez écrire ici : recharger nginx
```

🔍 **Observation** : ce play présente la **structure complète** d'un déploiement professionnel : préparatifs (`pre_tasks`), action principale (`tasks`), validation (`post_tasks`), réactions à un changement (`handlers`). L'ordre d'exécution est **garanti** par Ansible.

## 📚 Exercice 2 — `pre_tasks` (marqueur "predeploy")

Dans `pre_tasks:`, créez un fichier `/tmp/predeploy-{{ inventory_hostname }}.txt` contenant un timestamp via `ansible.builtin.copy` + `content:`. Indices :

- Module : `ansible.builtin.copy`
- `dest: "/tmp/predeploy-{{ inventory_hostname }}.txt"`
- `content: "predeploy {{ inventory_hostname }} at {{ ansible_date_time.iso8601 }}\n"`
- `mode: "0644"`

🔍 **Observation à anticiper** : `ansible_date_time` est un fact (collecté via `gather_facts`) qui contient l'heure du **managed node** au moment de la collecte (pas l'heure du control node).

## 📚 Exercice 3 — `tasks` (nginx + ouverture firewalld)

Dans `tasks:`, enchaînez 4 tâches :

1. **Installer nginx** : `ansible.builtin.dnf` avec `name: nginx`, `state: present`.
2. **Configurer la page d'accueil** : `ansible.builtin.copy` qui pose `/etc/nginx/conf.d/site.conf` avec un `server` minimal qui sert `Hello world from {{ inventory_hostname }}`. Cette tâche **doit notifier** le handler — ajoutez `notify: Recharger nginx` à la fin.
3. **Démarrer + activer nginx** : `ansible.builtin.systemd` avec `name: nginx`, `state: started`, `enabled: true`.
4. **Ouvrir HTTP dans firewalld** : `ansible.posix.firewalld` avec `service: http`, `permanent: true`, `immediate: true`, `state: enabled`.

🔍 **Observation à anticiper** : seule la tâche **(2)** notifie le handler — parce que c'est elle qui modifie la config nginx. Les 3 autres ne déclenchent pas de reload.

## 📚 Exercice 4 — `post_tasks` (smoke test + marqueur)

Dans `post_tasks:`, enchaînez 2 tâches :

1. **Tester** `http://localhost` avec `ansible.builtin.uri` : `url: http://localhost`, `status_code: 200`.
2. **Poser un marqueur** `/tmp/postdeploy-{{ inventory_hostname }}.txt` (même structure que le `predeploy` de l'exo 2).

🔍 **Observation à anticiper** : `post_tasks` s'exécute **après** que les handlers de `tasks:` aient tourné. C'est exactement ce qu'on veut pour un smoke test : on teste après le reload, pas avant.

## 📚 Exercice 5 — `handlers` (reload nginx)

Dans `handlers:`, ajoutez un handler unique :

```yaml
- name: Recharger nginx
  ansible.builtin.systemd:
    name: nginx
    state: reloaded
```

🔍 **Observation à anticiper** : un handler ressemble à une tâche normale, mais **ne s'exécute que si une tâche le `notify:`**. Si la tâche notifiante est en `ok` (idempotente, rien changé), le handler **ne tourne pas**. C'est exactement le comportement « restart-on-config-change » — voir lab 06 pour aller plus loin.

## 📚 Exercice 6 — Exécuter le playbook

Depuis la racine du repo :

```bash
ansible-playbook labs/ecrire-code/plays-et-tasks/playbook.yml
```

🔍 **Observation** : Ansible joue **toutes les tâches** sur **tous les hôtes** dans l'ordre `gather_facts → pre_tasks → tasks → handlers → post_tasks`. Sans `serial:`, les hôtes avancent **en parallèle** (par batch). La sortie console montre :

```text
PLAY [Déployer nginx ...] *********************************
TASK [Gathering Facts] ************************************
ok: [web1.lab]
ok: [web2.lab]
TASK [pre_tasks: predeploy] *******************************
changed: [web1.lab]
changed: [web2.lab]
... (toutes les tâches sur tous les hôtes) ...
RUNNING HANDLER [Recharger nginx] *************************
changed: [web1.lab]
changed: [web2.lab]
TASK [post_tasks: smoke test] *****************************
ok: [web1.lab]
ok: [web2.lab]
```

> Pour traiter **un hôte à la fois** (rolling update), il existe le mot-clé `serial:` — c'est l'objet du [lab 09](../09-ecrire-code-parallelisme-strategies/).

## 📚 Exercice 7 — Vérifier l'ordre d'exécution

Les fichiers marqueurs prouvent l'ordre `pre_tasks` → `tasks` → `handlers` → `post_tasks` :

```bash
ssh ansible@web1.lab 'sudo ls -la /tmp/predeploy-web1.lab.txt /tmp/postdeploy-web1.lab.txt'
```

🔍 **Observation** : le `mtime` du fichier `predeploy` doit être **strictement antérieur** au `mtime` du fichier `postdeploy`. Si vous ouvrez les deux fichiers, le `predeploy` a un timestamp **avant** le `postdeploy` — preuve que `pre_tasks` s'exécute bien avant `post_tasks`.

## 📚 Exercice 8 — Vérifier l'idempotence

Relancez :

```bash
ansible-playbook labs/ecrire-code/plays-et-tasks/playbook.yml
```

🔍 **Observation** : `PLAY RECAP` doit afficher `changed=0` partout. Et **important** : le handler `Recharger nginx` ne tourne pas (la tâche `(2)` est `ok` — pas de notification).

## 🔍 Observations à noter

- Ordre d'exécution **garanti** : `gather_facts` → `pre_tasks` (+ leurs handlers) → `roles` → `tasks` (+ leurs handlers) → `post_tasks` (+ leurs handlers).
- Les **handlers** s'exécutent **à la fin de leur section** par défaut. Pour les forcer plus tôt : `meta: flush_handlers` (lab 06).
- Une tâche est **`changed`** si elle a modifié l'état. Un handler ne se déclenche **que sur `changed`** (jamais sur `ok`).
- Le `notify:` sur la tâche `(2)` ne déclenche le handler **que si le fichier `site.conf` a réellement changé**. C'est ce qui rend le pattern « restart-on-config-change » idempotent.

## 🤔 Questions de réflexion

1. Que se passe-t-il si la tâche **(2)** échoue (config nginx invalide) ? Le handler est-il déclenché ? Les `post_tasks` tournent-ils ?

2. Vous voulez **forcer** le reload nginx **avant** le smoke test (sans attendre la fin de `tasks:`). Quel mécanisme Ansible utilise-t-on ? (Indice : `meta: flush_handlers`, lab 06.)

3. Pourquoi le smoke test (`uri:` dans `post_tasks`) tournerait-il **avant** le reload du handler si on l'avait mis dans `tasks:` au lieu de `post_tasks:` ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) reproduit le pattern `pre_tasks` / `tasks` / `post_tasks` / `handlers` sur `db1.lab` avec Apache (`httpd`) au lieu de nginx. Tests automatisés via `pytest+testinfra` :

```bash
pytest -v labs/ecrire-code/plays-et-tasks/challenge/tests/
```

## 💡 Pour aller plus loin

- **`meta: flush_handlers`** : forcer le déclenchement immédiat des handlers en attente, sans attendre la fin de la section. Voir le [lab 06 — handlers](../06-ecrire-code-handlers/).
- **`pre_tasks` défensif** : un `pre_tasks` qui appelle un endpoint `/health` interne et qui échoue **avant** la moindre modif — pattern classique en production.
- **Parallélisme et rolling updates** : `serial:`, `strategy:`, `max_fail_percentage:` sont introduits dans le [lab 09](../09-ecrire-code-parallelisme-strategies/).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/plays-et-tasks/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/plays-et-tasks/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/plays-et-tasks/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
