# Lab 17 — Lookups (récupérer des données externes)

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

🔗 [**Lookups Ansible : file, env, password, vars, hashi_vault**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/lookups/)

Un **lookup** récupère une donnée depuis une **source externe** au playbook : un
fichier local, une variable d'environnement, une commande shell, un mot de passe
généré, un secret stocké dans Vault. **L'exécution se fait côté control node**
(votre machine), pas managed node — c'est une différence cruciale avec les modules
classiques. La syntaxe : `{{ lookup('plugin_name', args) }}` ou `query('plugin_name')`
qui renvoie toujours une liste.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Lire** le contenu d'un fichier local avec `lookup('file', ...)`.
2. **Récupérer** une variable d'environnement avec `lookup('env', ...)`.
3. **Exécuter** une commande shell sur le control node avec `lookup('pipe', ...)`.
4. **Générer** un mot de passe via `lookup('password', ...)`.
5. **Distinguer** `lookup` (renvoie 1 valeur ou 1 string) de `query` (renvoie une liste).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
mkdir -p labs/ecrire-code/lookups/files
ansible db1.lab -b -m shell -a "rm -f /tmp/lookup-*.txt"
```

## 📚 Exercice 1 — `lookup('file', ...)` lire un fichier local

Créez `files/welcome.txt` :

```text
Bienvenue dans l environnement RHCE 2026
Ansible Core 2.20 + ansible-navigator
```

Créez `lab.yml` :

```yaml
---
- name: Demo lookup file
  hosts: db1.lab
  become: true
  tasks:
    - name: Lire le fichier local et le pousser sur db1
      ansible.builtin.copy:
        content: "{{ lookup('file', 'files/welcome.txt') }}"
        dest: /tmp/lookup-file.txt
        mode: "0644"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/lookups/lab.yml
ssh ansible@db1.lab 'cat /tmp/lookup-file.txt'
```

🔍 **Observation** : le contenu de `files/welcome.txt` (côté control node) a été
**lu localement** par Ansible et **injecté** dans `content:` du `copy:`. Le fichier
local **n'est jamais transféré** sur db1 — seul son contenu en string est utilisé.

**Différence avec `copy: src:`** : avec `src:`, Ansible **transfère** le fichier
binaire entièrement. Avec `lookup('file', ...)`, on lit la string et on l'utilise
en variable Jinja2. Pratique pour **injecter** un fichier dans un template plus
gros.

## 📚 Exercice 2 — `lookup('env', ...)` variable d'environnement

```yaml
- name: Lire l USER du control node
  ansible.builtin.debug:
    msg: "Vous etes connecte en tant que {{ lookup('env', 'USER') }}"

- name: Variable d env avec fallback si absente
  ansible.builtin.debug:
    msg: "MY_DEPLOY_KEY = {{ lookup('env', 'MY_DEPLOY_KEY') | default('non defini', true) }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/lookups/lab.yml
```

🔍 **Observation** : `USER` est défini dans votre shell, donc affiché. `MY_DEPLOY_KEY`
n'est probablement pas défini → renvoie une **string vide** (pas une erreur).
Le filtre `default('non defini', true)` (avec `true` comme 2e arg) traite la string
vide comme "absente".

**Cas d'usage** : récupérer un token de CI (`CI_JOB_TOKEN`), un chemin
(`HOME`), ou un secret injecté par Vault. Tester en local :

```bash
MY_DEPLOY_KEY=secret123 ansible-playbook labs/ecrire-code/lookups/lab.yml
```

## 📚 Exercice 3 — `lookup('pipe', ...)` exécuter une commande locale

```yaml
- name: Recuperer le SHA git du control node
  ansible.builtin.debug:
    msg: "Commit deploye : {{ lookup('pipe', 'git rev-parse --short HEAD 2>/dev/null || echo unknown') }}"

- name: Generer un timestamp local
  ansible.builtin.copy:
    content: "Deploy lance a {{ lookup('pipe', 'date --iso-8601=ns') }}\n"
    dest: /tmp/lookup-pipe.txt
    mode: "0644"
```

🔍 **Observation** : `pipe` exécute la commande **côté control node** et capture le
stdout. Le timestamp ou le SHA git sont **figés au moment du run** — utile pour
embarquer une **traçabilité** dans les fichiers déployés.

**Sécurité** : `pipe` exécute n'importe quelle commande shell. Ne **jamais** passer
une variable utilisateur non sanitizée dans `pipe` — risque d'injection shell.

## 📚 Exercice 4 — `lookup('password', ...)` génération de mot de passe

```yaml
- name: Generer un password persistant pour myapp
  ansible.builtin.set_fact:
    myapp_password: "{{ lookup('password', '/tmp/lookup-myapp-password.txt length=20 chars=ascii_letters,digits') }}"

- name: Afficher (a ne PAS faire en prod — log)
  ansible.builtin.debug:
    msg: "Generated password: {{ myapp_password }}"

- name: Pousser le password sur db1
  ansible.builtin.copy:
    content: "DB_PASSWORD={{ myapp_password }}\n"
    dest: /tmp/lookup-password-marker.txt
    mode: "0600"
```

🔍 **Observation** :

- **Premier run** : `lookup('password', ...)` **génère** un nouveau mot de passe et
  l'**écrit** dans `/tmp/lookup-myapp-password.txt` côté control node.
- **Runs suivants** : `lookup` **lit** le fichier existant — le password reste
  **identique** entre les runs.

C'est le pattern **génération idempotente de secrets** : générer une fois, persister,
réutiliser. Combiné avec **Ansible Vault** sur le fichier de stockage, c'est une
solution simple pour gérer des passwords sans WordPress / Vault HashiCorp.

## 📚 Exercice 5 — `lookup` vs `query`

```yaml
- name: lookup file (renvoie une string)
  ansible.builtin.debug:
    msg: "type lookup file : {{ lookup('file', 'files/welcome.txt') | type_debug }}"

- name: query lines (renvoie une liste — toujours)
  ansible.builtin.debug:
    msg: "type query lines : {{ query('lines', 'cat /etc/passwd') | type_debug }}"

- name: query file (renvoie une liste a 1 element)
  ansible.builtin.debug:
    msg: "type query file : {{ query('file', 'files/welcome.txt') | type_debug }}"
```

🔍 **Observation** :

- `lookup('file', ...)` → **string** (le contenu du fichier).
- `query('lines', 'cat /etc/passwd')` → **liste de lignes**.
- `query('file', ...)` → **liste à 1 élément** (toujours liste, même si une seule valeur).

**Règle** : utiliser `query` quand le résultat sert dans un `loop:` (qui veut une
liste). Utiliser `lookup` pour une valeur unique.

## 📚 Exercice 6 — Le piège : `lookup` est exécuté **chaque fois** la variable est lue

```yaml
- name: Lookup avec random — 1ere fois
  ansible.builtin.debug:
    msg: "uuid 1 : {{ lookup('pipe', 'uuidgen') }}"

- name: Lookup avec random — 2eme fois
  ansible.builtin.debug:
    msg: "uuid 2 : {{ lookup('pipe', 'uuidgen') }}"
```

🔍 **Observation** : les deux UUIDs sont **différents**. Chaque évaluation de `{{
lookup(...) }}` re-exécute le lookup.

**Pour figer la valeur** : capturer dans un `set_fact` :

```yaml
- name: Figer l uuid
  ansible.builtin.set_fact:
    deploy_uuid: "{{ lookup('pipe', 'uuidgen') }}"

- name: Reutiliser
  ansible.builtin.debug:
    msg: "Meme uuid partout : {{ deploy_uuid }} == {{ deploy_uuid }}"
```

## 🔍 Observations à noter

- **Lookups exécutent côté control node**, pas managed node.
- **`lookup` retourne une valeur**, **`query` retourne une liste** (toujours).
- **`lookup('file', ...)`** = lire un fichier local sans le transférer.
- **`lookup('env', ...)`** = lire une variable d'env du control node.
- **`lookup('pipe', ...)`** = exécuter une commande shell locale (attention sécurité).
- **`lookup('password', ...)`** = génération idempotente de password persisté.
- **Lookups sont ré-évalués** à chaque accès — utiliser `set_fact` pour figer.

## 🤔 Questions de réflexion

1. Vous voulez injecter le **commit SHA git** courant dans un fichier déployé sur
   tous les managed nodes pour traçabilité. Lookup `file`, `env`, ou `pipe` ?

2. `lookup('password', '~/secrets.txt')` génère un mot de passe persisté. Quelle
   est la **conséquence** si plusieurs développeurs utilisent ce playbook depuis
   leur machine ? (indice : le fichier est local au control node).

3. Vous voulez lire `/etc/passwd` du **managed node** dans une variable Ansible.
   `lookup('file', '/etc/passwd')` ne marche pas (lit côté control node). Quelle
   est l'alternative ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`lookup('hashi_vault', 'secret=...')`** : récupérer un secret depuis HashiCorp
  Vault. Authentification via `VAULT_TOKEN` env var.
- **`lookup('csvfile', ...)`** : extraction d'une cellule dans un CSV — pratique
  pour des configs métier en spreadsheet.
- **`lookup('template', ...)`** : rendre un template Jinja2 sans le déployer —
  utile pour pré-calculer un fichier qu'on injecte ailleurs.
- **`lookup('vars', 'dynamic_var_name')`** : déréférencer une variable dont le
  nom est lui-même dynamique (équivalent `vars[var_name]`).
- **Plugin custom** : on peut écrire son propre lookup en Python (`plugins/lookup/mon_lookup.py`).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/lookups/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/lookups/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/lookups/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
