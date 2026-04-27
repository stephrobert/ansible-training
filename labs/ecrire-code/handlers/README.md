# Lab 06 — Handlers (le pattern restart-on-config-change)

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

🔗 [**Handlers Ansible : notify, listen, flush_handlers et restart-on-config-change**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/handlers/)

Un **handler** est une **tâche réactive** : elle ne s'exécute **que si** une autre tâche l'a notifiée **et** que cette tâche est en `changed` (pas en `ok`). C'est le pattern que vous appliquerez 100 fois en production : « relance le service **uniquement si** sa config a changé ».

Les 4 mots-clés à connaître :

| Mot-clé | Où | Rôle |
| --- | --- | --- |
| **`notify:`** | sur une tâche | déclenche un handler nommé (un seul ou une liste) |
| **`handlers:`** | section dédiée du play | déclare les handlers (mêmes options qu'une tâche) |
| **`listen:`** | sur un handler | regroupe plusieurs handlers sous un **topic** abstrait |
| **`meta: flush_handlers`** | tâche spéciale | force l'exécution **immédiate** des handlers en attente |

Sans handler, vous écrivez `state: restarted` — qui redémarre **à chaque run**, donc casse l'idempotence. Avec handler, vous redémarrez **uniquement quand nécessaire**.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un handler simple notifié par une tâche.
2. Vérifier qu'un handler **ne se déclenche pas** quand sa tâche est `ok` (idempotence).
3. Notifier **plusieurs handlers** depuis une seule tâche.
4. Utiliser **`listen:`** pour découpler tâches et handlers via un topic.
5. Forcer l'exécution immédiate avec **`meta: flush_handlers`**.
6. Combiner **`validate:`** + handler pour ne **jamais** appliquer une config invalide.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible webservers -m ansible.builtin.ping
ansible webservers -b -m ansible.builtin.shell -a "rm -f /tmp/handler-*.txt"
```

Réponse attendue : 2 `pong`. Le second `ansible` nettoie d'éventuels marqueurs d'un run précédent.

## ⚙️ Arborescence cible

```text
labs/ecrire-code/handlers/
├── README.md           ← ce fichier
├── playbook.yml        ← À CRÉER — votre play avec handlers
└── challenge/
    ├── README.md       ← challenge final (déjà présent)
    └── tests/
        └── test_*.py   ← (déjà présent — pytest+testinfra)
```

## 📚 Exercice 1 — Squelette du play

Créez `labs/ecrire-code/handlers/playbook.yml` :

```yaml
---
- name: Configurer httpd avec restart-on-config-change
  hosts: webservers
  become: true

  tasks:
    # Tâches qui notifient le handler

  handlers:
    # Handler qui reload httpd
```

🔍 **Observation** : `handlers:` est une **section sœur** de `tasks:` (au même niveau, pas dedans). Les handlers ne s'exécutent jamais d'eux-mêmes — il faut une tâche qui les `notify:`.

## 📚 Exercice 2 — Premier handler simple (notify)

Dans `tasks:`, ajoutez 3 tâches :

1. **Installer httpd** : `ansible.builtin.dnf` avec `name: httpd`, `state: present`.
2. **Démarrer + activer httpd** : `ansible.builtin.systemd` avec `name: httpd`, `state: started`, `enabled: true`.
3. **Modifier `httpd.conf`** : `ansible.builtin.lineinfile` avec :
   - `path: /etc/httpd/conf/httpd.conf`
   - `regexp: '^#?\\s*ServerTokens\\s+'`
   - `line: 'ServerTokens Prod'`
   - **`notify: Reload httpd`** ← la magie

Dans `handlers:`, ajoutez :

```yaml
- name: Reload httpd
  ansible.builtin.systemd:
    name: httpd
    state: reloaded
```

🔍 **Observation à anticiper** : la tâche **(3)** notifie le handler `Reload httpd`. Le nom du `notify:` doit correspondre **exactement** au `name:` du handler — sensible à la casse, espaces compris.

## 📚 Exercice 3 — Lancer et observer

Depuis la racine :

```bash
ansible-playbook labs/ecrire-code/handlers/playbook.yml
```

🔍 **Observation** — sortie console attendue (extrait) :

```text
TASK [Modifier httpd.conf] *************************
changed: [web1.lab]                ← la tâche est "changed"
changed: [web2.lab]

RUNNING HANDLER [Reload httpd] *********************   ← le handler tourne !
changed: [web1.lab]
changed: [web2.lab]

PLAY RECAP *****************************************
web1.lab    : ok=4    changed=2  ...
```

Le handler `Reload httpd` s'est exécuté **après** toutes les tâches du play. C'est le **comportement par défaut** : les handlers sont mis en file d'attente et **vidés à la fin de leur section**.

## 📚 Exercice 4 — Vérifier que le handler **ne se redéclenche pas**

Relancez **immédiatement** la même commande :

```bash
ansible-playbook labs/ecrire-code/handlers/playbook.yml
```

🔍 **Observation** : cette fois, **pas de bandeau `RUNNING HANDLER`**. Le `PLAY RECAP` affiche `changed=0`. Pourquoi ?

- La tâche **(3)** est `ok` (la ligne est déjà conforme).
- **Pas de `changed` → pas de notification → pas de handler.**

C'est exactement ce qu'on veut : on **ne reload httpd que si la config a vraiment changé**. Vous venez de voir le pattern restart-on-config-change appliqué.

## 📚 Exercice 5 — Vérifier l'effet du reload

```bash
curl -s -I http://web1.lab | grep -i ^Server:
```

🔍 **Observation** : le header `Server:` doit afficher `Apache` (sans version) — preuve que `ServerTokens Prod` est appliqué **et** que httpd a bien été rechargé. Avant le handler, vous auriez vu `Apache/2.4.x (AlmaLinux)` (la version par défaut).

## 📚 Exercice 6 — Notifier **plusieurs handlers** depuis une tâche

`notify:` accepte une **liste**. Modifiez la tâche **(3)** pour notifier deux handlers, et ajoutez le second :

```yaml
- name: Modifier httpd.conf (ServerTokens)
  ansible.builtin.lineinfile:
    path: /etc/httpd/conf/httpd.conf
    regexp: '^#?\s*ServerTokens\s+'
    line: 'ServerTokens Prod'
  notify:
    - Reload httpd
    - Notifier journal local
```

Dans `handlers:`, ajoutez le second :

```yaml
- name: Notifier journal local
  ansible.builtin.lineinfile:
    path: /tmp/handler-journal.txt
    line: "Config httpd modifiée le {{ ansible_date_time.iso8601 }}"
    create: true
    mode: "0644"
```

> ⚠️ **Avant de relancer**, modifiez la valeur du `line:` (par ex. `ServerTokens Major`) pour forcer un `changed` — sinon les handlers ne se déclencheront pas. Puis relancez avec la valeur d'origine pour rétablir l'état.

🔍 **Observation** : quand la tâche change, **les deux handlers tournent**, dans l'ordre où ils sont déclarés dans `handlers:` (pas dans l'ordre du `notify:`).

## 📚 Exercice 7 — Découpler avec `listen:` (topic)

`listen:` permet d'écouter un **topic abstrait** au lieu d'un nom de handler précis. Pratique pour ajouter un handler sans toucher aux tâches existantes.

Refactorisez l'exercice 6 :

```yaml
tasks:
  - name: Modifier httpd.conf (ServerTokens)
    ansible.builtin.lineinfile:
      path: /etc/httpd/conf/httpd.conf
      regexp: '^#?\s*ServerTokens\s+'
      line: 'ServerTokens Prod'
    notify: httpd-config-changed       # un topic, pas un nom

handlers:
  - name: Reload httpd
    listen: httpd-config-changed       # ce handler écoute le topic
    ansible.builtin.systemd:
      name: httpd
      state: reloaded

  - name: Notifier journal local
    listen: httpd-config-changed       # celui-ci aussi
    ansible.builtin.lineinfile:
      path: /tmp/handler-journal.txt
      line: "Config httpd modifiée le {{ ansible_date_time.iso8601 }}"
      create: true
      mode: "0644"
```

🔍 **Observation** : la tâche notifie **un seul nom** (`httpd-config-changed`), mais **deux handlers** se déclenchent parce qu'ils écoutent ce topic. Si demain vous ajoutez un troisième handler sur le même topic, **aucune tâche à modifier**. C'est le découplage.

## 📚 Exercice 8 — Forcer l'exécution immédiate avec `meta: flush_handlers`

Par défaut, les handlers tournent **à la fin de la section** (`tasks` ici). Mais parfois, vous voulez les forcer **avant** une tâche suivante — typiquement, valider la nouvelle config dans le même play.

Ajoutez `meta: flush_handlers` **juste après** la tâche `(3)`, puis un smoke test :

```yaml
tasks:
  - name: Modifier httpd.conf (ServerTokens)
    ansible.builtin.lineinfile:
      path: /etc/httpd/conf/httpd.conf
      regexp: '^#?\s*ServerTokens\s+'
      line: 'ServerTokens Prod'
    notify: Reload httpd

  - name: Forcer le reload immédiat
    ansible.builtin.meta: flush_handlers

  - name: Smoke test après reload
    ansible.builtin.uri:
      url: http://localhost
      status_code: 200
```

🔍 **Observation** : sans `flush_handlers`, le `uri:` testerait nginx **avant** le reload — donc avec l'ancienne config. Avec `flush_handlers`, l'ordre devient : modif → reload → test. C'est le pattern qu'on retrouve sur les déploiements de configs critiques (sshd, postgresql).

## 📚 Exercice 9 — Combiner `validate:` + handler (filet de sécurité)

Le module `lineinfile` (et `template`) accepte un argument `validate:` qui exécute une commande sur le fichier **avant** de l'écrire en place. Si la commande échoue, le fichier original n'est **pas** remplacé — et le handler n'est **pas** notifié (puisque `changed=false`).

```yaml
- name: Modifier httpd.conf avec validation syntaxique
  ansible.builtin.lineinfile:
    path: /etc/httpd/conf/httpd.conf
    regexp: '^#?\s*ServerTokens\s+'
    line: 'ServerTokens Prod'
    validate: 'apachectl -t -f %s'        # %s = chemin du fichier temporaire
  notify: Reload httpd
```

🔍 **Observation** : si vous mettez volontairement `line: 'ServerTokens Garbage'` (invalide), `apachectl -t` échoue, le fichier d'origine reste intact, **et** le handler n'est pas déclenché. C'est le **filet de sécurité** qui empêche d'appliquer une config invalide en production.

> 💡 **Note pratique** : sur `httpd.conf`, `validate:` peut échouer parce que le fichier inclut `/etc/httpd/conf.d/*.conf` non disponibles dans le contexte de validation. Le mécanisme reste valide pour des configs autonomes (`sshd_config`, `nginx.conf` standalone, etc.).

## 🔍 Observations à noter

- Un handler s'exécute **uniquement si** une tâche le notifie **et** est en `changed`. Pas de `changed` → pas de handler.
- Les handlers sont **dédupliqués** : si 5 tâches notifient le même handler, il ne tourne qu'**une fois**.
- **`listen:`** = topic abstrait. Permet de découpler tâches et handlers.
- **`meta: flush_handlers`** = vide la file d'attente immédiatement. À utiliser quand l'ordre `tâche → reload → test` doit être strict dans le même play.
- **`validate:`** est le filet de sécurité avant écriture. Combiné avec un handler, vous ne reload **jamais** un service sur une config cassée.
- Un handler **rappelé en échec** stoppe le play comme une tâche normale. Gardez les handlers simples (un reload, un log) — pas de logique complexe dedans.

## 🤔 Questions de réflexion

1. Vous avez un play qui modifie 5 fichiers de config nginx (vhosts, main, modules, etc.). Vous voulez **un seul reload** à la fin. Combien de handlers déclarez-vous ? Combien de notifications ?

2. Vous voulez relancer **immédiatement** un service après modification d'une config, mais avant la tâche suivante. Quel mot-clé utiliser, et pourquoi pas un `state: restarted` direct ?

3. Comment garantir qu'un handler **n'applique jamais** une config invalide ? Cite les **deux** mécanismes complémentaires.

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) consolide les exercices 6-8 sur `db1.lab` : deux handlers, une tâche, et `meta: flush_handlers` pour valider la config dans le même play. Tests automatisés via `pytest+testinfra` :

```bash
pytest -v labs/ecrire-code/handlers/challenge/tests/
```

## 💡 Pour aller plus loin

- **`force_handlers: true`** au niveau play : exécute les handlers en attente **même si une tâche échoue** ensuite. Pratique pour ne pas laisser un service avec une config moitié-modifiée.
- **Handlers dans un rôle** : les handlers d'un rôle vivent dans `roles/<role>/handlers/main.yml` — accessibles par `notify:` depuis n'importe quelle tâche du rôle, et même depuis l'extérieur.
- **Variables dans `notify:`** : `notify: "{{ service_handler_name }}"` — permet de paramétrer le handler à appeler. Utile pour des rôles génériques (notifier `Reload nginx` ou `Reload apache` selon une variable).
- **Pattern saga** : `pre_tasks` (snapshot DB) → `tasks` (modif config) → `meta: flush_handlers` (reload) → `post_tasks` (smoke test) → handler `Restaurer snapshot` notifié uniquement en cas d'erreur. Voir lab 23 (block/rescue/always).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/handlers/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/handlers/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/handlers/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
