# Lab 18 — Jinja2 syntaxe de base (interpolation, logique, whitespace)

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

🔗 [**Jinja2 syntaxe de base Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/jinja2-base/)

Jinja2 est le **moteur de templating** utilisé par Ansible (et de nombreux autres
outils Python : Flask, Django, Salt). Il offre **3 syntaxes** :

- **`{{ expression }}`** : interpolation d'une expression (variable, filtre, calcul).
- **`{% statement %}`** : logique (boucle `for`, condition `if`, set, etc.).
- **`{# commentaire #}`** : commentaire jinja2 — **non rendu** dans la sortie.

Le **whitespace control** (`{%-`, `-%}`, `lstrip_blocks`, `trim_blocks`) gère
l'apparition d'espaces et sauts de ligne autour des blocs `{% %}` — un piège
classique des fichiers de config générés.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Interpoler** des variables avec `{{ }}` et appliquer des filtres.
2. **Boucler** avec `{% for %}` et conditionner avec `{% if %}`.
3. **Commenter** avec `{# #}` (jinja2) vs `#` (commentaire de fichier final).
4. **Maîtriser** le whitespace control (`{%- -%}`, `lstrip_blocks`, `trim_blocks`).
5. **Diagnostiquer** un template qui produit des sauts de ligne parasites.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
mkdir -p labs/ecrire-code/jinja2-base/templates
ansible db1.lab -b -m shell -a "rm -f /tmp/jinja-*.txt"
```

## 📚 Exercice 1 — Interpolation simple `{{ }}`

Créez `templates/simple.j2` :

```jinja
Bonjour {{ name | default('inconnu') }} !
Vous avez {{ items | length }} items.
Premier item : {{ items[0] | upper }}.
```

Créez `lab.yml` :

```yaml
---
- name: Demo jinja2 base
  hosts: db1.lab
  become: true
  vars:
    name: Alice
    items: [un, deux, trois]
  tasks:
    - name: Generer le fichier depuis le template simple
      ansible.builtin.template:
        src: templates/simple.j2
        dest: /tmp/jinja-simple.txt
        mode: "0644"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/jinja2-base/lab.yml
ssh ansible@db1.lab 'cat /tmp/jinja-simple.txt'
```

🔍 **Observation** :

```text
Bonjour Alice !
Vous avez 3 items.
Premier item : UN.
```

`{{ }}` interpole l'expression. Les **filtres** (`| upper`, `| length`, `| default`)
s'appliquent comme dans un `debug:` d'Ansible.

## 📚 Exercice 2 — Boucles `{% for %}`

Créez `templates/loop.j2` :

```jinja
[users]
{% for user in users %}
{{ user.name }} = {{ user.uid }}
{% endfor %}
```

Modifiez `lab.yml` pour ajouter :

```yaml
vars:
  users:
    - { name: alice, uid: 1001 }
    - { name: bob, uid: 1002 }
    - { name: charlie, uid: 1003 }
```

Et la tâche :

```yaml
- name: Generer le fichier loop
  ansible.builtin.template:
    src: templates/loop.j2
    dest: /tmp/jinja-loop.txt
    mode: "0644"
```

**Lancez et inspectez** :

```bash
ansible-playbook labs/ecrire-code/jinja2-base/lab.yml
ssh ansible@db1.lab 'cat -A /tmp/jinja-loop.txt'  # cat -A montre les sauts de ligne
```

🔍 **Observation** : output (avec `cat -A`) :

```text
[users]$
$
alice = 1001$
$
bob = 1002$
$
charlie = 1003$
$
```

**Lignes vides parasites** entre les itérations ! C'est le **piège du whitespace** —
le `\n` après `{% for %}` reste dans la sortie.

## 📚 Exercice 3 — Whitespace control avec `{%- -%}`

Modifiez `templates/loop.j2` pour ajouter `-` dans les blocs jinja :

```jinja
[users]
{% for user in users -%}
{{ user.name }} = {{ user.uid }}
{% endfor %}
```

🔍 **Observation** : `{%- ... -%}` retire les espaces/sauts de ligne **avant** ou
**après** le bloc. `{% for user in users -%}` retire le `\n` qui suivrait. Output
plus propre :

```text
[users]
alice = 1001
bob = 1002
charlie = 1003
```

**Convention** :

- **`{%-`** retire les whitespaces **avant** le bloc.
- **`-%}`** retire les whitespaces **après** le bloc.

## 📚 Exercice 4 — `lstrip_blocks` et `trim_blocks` (config globale)

Au lieu de mettre `-` partout, on peut activer ces options **au niveau du module
template** :

```yaml
- name: Generer avec whitespace control auto
  ansible.builtin.template:
    src: templates/loop.j2
    dest: /tmp/jinja-loop-clean.txt
    mode: "0644"
    lstrip_blocks: true
    trim_blocks: true
```

| Option | Effet |
|---|---|
| **`trim_blocks: true`** | Retire le **premier `\n` après** un bloc `{% %}`. |
| **`lstrip_blocks: true`** | Retire les **whitespaces avant** un bloc `{% %}` (en début de ligne). |

🔍 **Observation** : avec ces deux options, votre template peut être **indenté**
proprement (lecture facile) sans que l'indentation se retrouve dans la sortie :

```jinja
{% for user in users %}
    {% if user.enabled %}
{{ user.name }} = {{ user.uid }}
    {% endif %}
{% endfor %}
```

Les `    {% if %}` sont **lstripés**, les `\n` après `{% endif %}` sont **trim_blocked**.
Output identique à du jinja2 sans indentation.

**Convention RHCE** : **toujours** `lstrip_blocks: true` + `trim_blocks: true` sur
les modules `template:`.

## 📚 Exercice 5 — Commentaires `{# #}` vs `#`

```jinja
{# Ce commentaire est jinja2 - ne sera PAS dans la sortie #}
[server]
# Ce commentaire INI restera dans la sortie
host = {{ ansible_default_ipv4.address }}
```

🔍 **Observation** : `{# #}` est un commentaire jinja2 (filtré au rendu). `#` est
juste du texte (qui se retrouve dans la sortie). Utilisez `{# #}` pour des **notes
de template** que l'utilisateur final ne doit pas voir.

## 📚 Exercice 6 — Conditions `{% if %}` et `{% set %}`

```jinja
{% set environment = ansible_env.MYAPP_ENV | default('dev') %}
[app]
env = {{ environment }}

{% if environment == 'prod' %}
log_level = WARN
debug = false
{% elif environment == 'staging' %}
log_level = INFO
debug = false
{% else %}
log_level = DEBUG
debug = true
{% endif %}
```

🔍 **Observation** : `{% set %}` crée une variable **locale au template**. `{% if
elif else endif %}` permet le branchement classique. Pratique pour générer des
configs **adaptées à l'environnement** depuis un seul template.

## 📚 Exercice 7 — Le piège : `{{ }}` à l'intérieur d'un `when:` Ansible

```yaml
# ❌ Mauvais
- name: Action conditionnee
  ansible.builtin.debug:
    msg: "OK"
  when: "{{ ansible_distribution == 'AlmaLinux' }}"   # ❌

# ✅ Bon
- name: Action conditionnee
  ansible.builtin.debug:
    msg: "OK"
  when: ansible_distribution == 'AlmaLinux'   # ✅
```

🔍 **Observation** : dans `when:`, **pas de `{{ }}`** — l'expression est déjà Jinja2.
Ansible 2.16+ affiche un warning si vous mettez les `{{ }}` quand même. C'est une
règle systématique pour `when:`, `failed_when:`, `changed_when:`, `loop_control:
when:`.

## 🔍 Observations à noter

- **`{{ expression }}`** = interpolation, **`{% statement %}`** = logique, **`{# commentaire #}`** = note jinja2.
- **`{%- -%}`** (avec tirets) = retire whitespaces autour du bloc.
- **`lstrip_blocks: true`** + **`trim_blocks: true`** sur `template:` = whitespace control automatique.
- **`{% set %}`** crée une variable locale au template.
- **Pas de `{{ }}`** dans `when:`, `failed_when:`, `changed_when:`.
- **`{# #}`** = commentaire jinja2 (filtré), **`#`** = commentaire du fichier final (gardé).

## 🤔 Questions de réflexion

1. Vous générez un fichier `/etc/hosts` avec une boucle sur les `groups['all']`.
   Sans `lstrip_blocks` et `trim_blocks`, qu'est-ce qui se passe avec votre
   indentation jinja2 ?

2. Quelle est la différence sémantique entre `{% set x = expr %}` (dans un template)
   et `set_fact: x: "{{ expr }}"` (dans un play) ?

3. Vous voulez **garder le `\n`** après un `{% if %}` (parce que c'est intentionnel).
   Comment override `trim_blocks: true` localement ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`{% include %}`** : inclure un autre fichier `.j2` dans le template courant.
  Permet de **factoriser** des fragments réutilisables (header, footer).
- **`{% extends %}`** + **`{% block %}`** : héritage de templates (comme Django).
  Surcouche pour les très gros projets — souvent overkill pour Ansible.
- **`{% raw %}` / `{% endraw %}`** : zone où Jinja2 **n'interprète pas** `{{ }}` —
  utile quand vous générez un fichier qui contient lui-même du jinja2 (ex : un
  template Helm qui sera rendu plus tard).
- **`autoescape: true`** : échappement automatique des caractères HTML — utile
  uniquement si vous générez du HTML avec des données utilisateur.
- **Tests jinja2** (lab 28) : `{% if x is defined %}`, `{% if x is mapping %}`, etc.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/jinja2-base/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/jinja2-base/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/jinja2-base/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
