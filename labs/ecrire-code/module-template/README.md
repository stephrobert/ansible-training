# Lab 29 — Module `template:` (`validate`, `backup`, `lstrip_blocks`)

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

🔗 [**Module template Ansible : validate, backup, lstrip_blocks**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/module-template/)

`ansible.builtin.template:` génère un fichier sur le managed node à partir d'un
template Jinja2 du control node + variables Ansible. C'est le module **n°1** pour
les fichiers de configuration : nginx.conf, postgresql.conf, sshd_config,
prometheus.yml.

Différences clés avec `copy:` :

- **`template:`** rend le Jinja2 (interpolation, filtres, conditions, boucles).
- **`copy:`** transfère le contenu **tel quel** (pas d'interpolation).

Options critiques RHCE :

- **`validate:`** : valide la syntaxe **avant** d'écraser la cible.
- **`backup: true`** : sauvegarde l'ancienne version.
- **`lstrip_blocks: true`** + **`trim_blocks: true`** : whitespace control.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Générer** un fichier de config depuis un template Jinja2.
2. **Valider** la syntaxe avant écriture (pattern critique pour `sshd_config`, `nginx.conf`).
3. **Sauvegarder** automatiquement avec `backup: true`.
4. **Maîtriser** le whitespace control via `lstrip_blocks` + `trim_blocks`.
5. **Appliquer** les bonnes pratiques (mode, owner, group) pour des configs déployées.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
mkdir -p labs/ecrire-code/module-template/templates
ansible db1.lab -b -m shell -a "rm -f /etc/myapp.conf*; rm -f /tmp/lab-template-*"
```

## 📚 Exercice 1 — Premier template

Créez `templates/myapp.conf.j2` :

```jinja
[server]
host = {{ server.host }}
port = {{ server.port }}
workers = {{ server.workers }}

[database]
url = {{ database.url }}
pool_size = {{ database.pool_size }}
```

Créez `lab.yml` :

```yaml
---
- name: Demo template basique
  hosts: db1.lab
  become: true
  vars:
    server:
      host: "0.0.0.0"
      port: 8080
      workers: 4
    database:
      url: "postgres://db1.lab/myapp"
      pool_size: 10
  tasks:
    - name: Generer myapp.conf depuis template
      ansible.builtin.template:
        src: templates/myapp.conf.j2
        dest: /etc/myapp.conf
        owner: root
        group: root
        mode: "0644"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/module-template/lab.yml
ssh ansible@db1.lab 'cat /etc/myapp.conf'
```

🔍 **Observation** : le template a été **rendu** (variables interpolées, sections
INI générées). Comparé à `copy:`, vous n'auriez pas pu faire ça avec un fichier
statique.

## 📚 Exercice 2 — `backup: true` (sauvegarde automatique)

Modifiez `lab.yml` pour ajouter `backup: true` :

```yaml
- name: Generer avec backup
  ansible.builtin.template:
    src: templates/myapp.conf.j2
    dest: /etc/myapp.conf
    backup: true
    owner: root
    group: root
    mode: "0644"
```

**Modifiez le template** (changer `port: 8080` → `port: 9090`) puis relancez :

```bash
ansible-playbook labs/ecrire-code/module-template/lab.yml
ssh ansible@db1.lab 'ls -la /etc/myapp.conf*'
```

🔍 **Observation** : un fichier `myapp.conf.<timestamp>~` est créé avant l'écrasement.
Format : `<dest>.<YYYY-MM-DD@HH:MM:SS~>`. Pratique pour **rollback rapide** :

```bash
ssh ansible@db1.lab 'sudo cp /etc/myapp.conf.2026-04-25@21:00:00~ /etc/myapp.conf'
```

**`backup: true`** est gratuit (juste un cp local) — **toujours** activer sur les
fichiers de config critiques.

## 📚 Exercice 3 — `validate:` (rejeter une config invalide)

Pattern critique pour `sshd_config`, `nginx.conf`, `sudoers` — un fichier mal
formé verrouille le système.

**Cas SSH** : sshd ne démarre plus si `sshd_config` est invalide → vous perdez
l'accès SSH au serveur.

```yaml
- name: Generer sshd_config avec validation
  ansible.builtin.template:
    src: templates/sshd_config.j2
    dest: /etc/ssh/sshd_config
    backup: true
    owner: root
    group: root
    mode: "0600"
    validate: 'sshd -t -f %s'
  notify: Reload sshd

handlers:
  - name: Reload sshd
    ansible.builtin.systemd_service:
      name: sshd
      state: reloaded
```

🔍 **Observation** :

- **`validate: 'sshd -t -f %s'`** : Ansible **rend** le template dans un fichier
  temporaire, lance `sshd -t -f /tmp/<temp>` pour vérifier la syntaxe.
- Si `sshd -t` retourne **0** (OK) → la config est écrite, le handler est notifié.
- Si `sshd -t` retourne **!= 0** (invalide) → le fichier temporaire est jeté,
  `/etc/ssh/sshd_config` reste **intact**, la tâche **failed**.

**Le `%s`** est remplacé par le chemin du fichier temporaire. **Obligatoire** dans
la commande de validation.

**Cas nginx** : `validate: 'nginx -t -c %s'`.
**Cas sudoers** : `validate: 'visudo -cf %s'`.

## 📚 Exercice 4 — `lstrip_blocks` + `trim_blocks` (whitespace control)

Créez `templates/loop.j2` :

```jinja
[users]
{% for user in users %}
    {% if user.enabled %}
{{ user.name }} = {{ user.uid }}
    {% endif %}
{% endfor %}
```

Sans whitespace control, le rendu inclura les indentations et sauts de ligne
parasites. Avec :

```yaml
- name: Template avec whitespace control
  ansible.builtin.template:
    src: templates/loop.j2
    dest: /tmp/lab-template-clean.txt
    mode: "0644"
    lstrip_blocks: true
    trim_blocks: true
```

🔍 **Observation** :

- **`lstrip_blocks: true`** : retire les espaces **avant** les blocs `{% %}` en début de ligne.
- **`trim_blocks: true`** : retire le `\n` **après** les blocs `{% %}`.

Combinés, vous pouvez **indenter votre template** pour la lisibilité sans que
l'indentation se retrouve dans la sortie. Output propre :

```text
[users]
alice = 1001
charlie = 1003
```

**Convention RHCE** : **toujours** activer ces deux options.

## 📚 Exercice 5 — `copy:` + `content:` vs `template:`

Question : quand préférer l'un ou l'autre ?

```yaml
# copy + content : pas d interpolation, pour fichiers TRES courts
- ansible.builtin.copy:
    content: "Static content\n"
    dest: /tmp/static.txt

# template : interpolation, pour fichiers de config
- ansible.builtin.template:
    src: templates/dynamic.j2
    dest: /tmp/dynamic.txt
```

| Cas | Module recommandé |
|---|---|
| Fichier statique court (1-3 lignes, pas de variable) | `copy: content:` |
| Fichier statique long sans variable | `copy: src:` |
| Fichier avec **1 variable interpolée** | `template:` |
| Fichier avec boucles, conditions, filtres | `template:` (obligatoire) |

🔍 **Observation** : si vous avez **un seul** `{{ var }}`, passer à `template:`. Le
coût est nul, le bénéfice est **scalability** (plus tard vous ajouterez d'autres
interpolations).

## 📚 Exercice 6 — Le piège : variables non définies dans un template

```jinja
{# templates/strict.j2 #}
[app]
host = {{ app_host }}
port = {{ app_port }}
debug = {{ app_debug }}
```

Si une seule variable manque (`app_debug` non défini), Jinja2 **plante** avec :

```text
'app_debug' is undefined
```

**Solution 1** : `default()` dans le template.

```jinja
debug = {{ app_debug | default(false) }}
```

**Solution 2** : `assert:` au début du play pour valider toutes les variables.

```yaml
- ansible.builtin.assert:
    that:
      - app_host is defined
      - app_port is defined and app_port is integer
      - app_debug is defined
    fail_msg: "Variables app_* manquantes"
```

**Solution 3** : `vars:` du play avec valeurs par défaut.

🔍 **Observation** : préférer `assert:` + variables explicites — un échec **précoce
et clair** vaut mieux qu'une erreur cryptique au milieu du template.

## 🔍 Observations à noter

- **`template:`** rend le Jinja2 ; **`copy:`** transfère sans interprétation.
- **`backup: true`** = filet de sécurité gratuit, toujours activer sur les configs critiques.
- **`validate:`** = pattern obligatoire pour `sshd_config`, `nginx.conf`, `sudoers`.
- **`lstrip_blocks: true`** + **`trim_blocks: true`** = whitespace control standard.
- **`mode: "0644"`** (avec guillemets) — sinon YAML parse `0644` en décimal.
- **Variables non définies** dans un template → erreur au rendu — utiliser `default()` ou `assert:`.

## 🤔 Questions de réflexion

1. Vous générez `/etc/sshd_config` via `template:`. Pourquoi `validate: 'sshd -t -f
   %s'` est-il **plus important** ici que sur `/etc/motd` ?

2. `template:` réécrit le fichier **complètement** à chaque run. Quel est le
   risque sur un fichier que **l'utilisateur** modifie manuellement (config user
   vs config managée) ?

3. `lstrip_blocks: true` + `trim_blocks: true` peuvent-ils introduire un bug si
   votre template a **volontairement** des espaces / `\n` significatifs ? Donner
   un exemple.

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`block_start_string` / `block_end_string`** : changer les délimiteurs `{% %}`
  pour générer un fichier qui contient **lui-même** du jinja2 (ex : un Helm chart).
- **`force: false`** : ne réécrit pas si le fichier existe déjà — pour des config
  initiales que l'opérateur peut modifier.
- **Pattern `template + lineinfile`** : `template:` pour la base, `lineinfile:`
  pour des overrides ponctuels que l'opérateur peut ajouter — ne pas mélanger
  sinon `template:` écrase tout.
- **`vault_decrypt` au runtime** : un template peut contenir
  `{{ lookup('vault_password_files', 'mypassword') }}` pour injecter un secret
  Vault déchiffré au rendu.
- **Lab 30 (lineinfile vs template)** : comparaison détaillée des deux approches.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/module-template/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/module-template/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/module-template/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
