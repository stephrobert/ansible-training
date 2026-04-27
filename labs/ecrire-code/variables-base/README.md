# Lab 12 — Variables (déclaration et portées)

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

🔗 [**Variables Ansible : déclaration, portées et types simples**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/variables-base/)

Ansible offre **5 emplacements principaux** pour déclarer une variable : `vars:` (dans
le play), `vars_files:` (fichiers externes), `group_vars/`, `host_vars/`, et
`--extra-vars` (CLI). Chaque emplacement a une **priorité** différente — comprendre
ces priorités est crucial pour ne pas être surpris quand une variable "ne prend pas
la valeur attendue".

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Déclarer** une variable au niveau play (`vars:`).
2. **Externaliser** des variables dans un fichier (`vars_files:`).
3. **Surcharger** depuis la CLI avec `--extra-vars` et observer la priorité absolue.
4. **Distinguer** les types simples (string, int, float, bool) et leurs pièges YAML.
5. **Diagnostiquer** un cas où une variable ne prend pas la valeur attendue.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
mkdir -p labs/ecrire-code/variables-base/vars
ansible web1.lab -m ping
```

## 📚 Exercice 1 — Variable au niveau play (`vars:`)

Créez `lab.yml` :

```yaml
---
- name: Demo vars du play
  hosts: web1.lab
  become: true
  vars:
    app_version: "1.0"
    app_env: "dev"
  tasks:
    - name: Afficher les variables
      ansible.builtin.debug:
        msg: "version={{ app_version }} env={{ app_env }}"
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml
```

🔍 **Observation** : la sortie debug affiche `version=1.0 env=dev`. Ces variables
n'existent **que pour ce play** — un autre play du même fichier ne les verrait pas.

## 📚 Exercice 2 — Externaliser dans `vars_files:`

Créez `vars/app.yml` :

```yaml
---
app_port: 80
app_protocol: "http"
app_replicas: 3
```

Modifiez `lab.yml` pour ajouter `vars_files:` :

```yaml
---
- name: Demo vars + vars_files
  hosts: web1.lab
  become: true
  vars:
    app_version: "1.0"
    app_env: "dev"
  vars_files:
    - vars/app.yml
  tasks:
    - name: Afficher toutes les variables
      ansible.builtin.debug:
        msg: |
          version={{ app_version }}
          env={{ app_env }}
          port={{ app_port }}
          protocol={{ app_protocol }}
          replicas={{ app_replicas }}
```

**Lancez** :

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml
```

🔍 **Observation** : les variables de `vars_files:` sont **chargées en plus** des
`vars:` du play — pas de conflit, complémentarité. **Pourquoi externaliser ?**

- Réutiliser le même fichier dans plusieurs plays.
- Versionner les configs métier (DEV/STAGING/PROD) dans des fichiers séparés.
- Permettre à un opérateur de modifier `vars/app.yml` sans toucher au playbook.

## 📚 Exercice 3 — Override avec `--extra-vars` (priorité absolue)

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml \
  --extra-vars "app_env=prod app_version=2.0"
```

🔍 **Observation** : `app_env` et `app_version` ont changé (`prod`, `2.0`) — mais
`app_port` reste à `80`, `app_protocol` à `http`, `app_replicas` à `3` (vous ne les
avez pas surchargés).

**`--extra-vars` (niveau 22)** est la **priorité absolue** dans la précédence Ansible.
Aucun autre emplacement ne peut le surcharger. C'est l'**arme du dépannage en
production** : un opérateur force une valeur précise sans modifier le code.

**Variantes utiles** de `--extra-vars` :

```bash
# JSON (pour des valeurs complexes)
--extra-vars '{"app_env":"prod","app_version":"2.0","tags":["v2","stable"]}'

# Depuis un fichier
--extra-vars "@vars/prod-override.yml"
```

## 📚 Exercice 4 — Pièges YAML sur les types

YAML est strict mais surprend parfois. Créez `vars/types.yml` :

```yaml
---
# String simple
app_name: "myapp"

# Integer (pas de guillemets)
app_port: 8080

# Boolean (yes/no rejetes en YAML 1.2 strict — utiliser true/false)
app_debug: true

# Float
app_ratio: 0.5

# String qui RESSEMBLE a un nombre — guillemets obligatoires sinon perte du 0 leading
app_id: "0042"

# String qui ressemble a un boolean (piege classique)
app_yes_no: "yes"  # Sans guillemets, devient bool true en YAML 1.1
```

Modifiez `lab.yml` pour charger `vars/types.yml` et afficher les types via le filtre
`type_debug` :

```yaml
- name: Afficher type Python de chaque variable
  ansible.builtin.debug:
    msg: "{{ item }} = {{ vars[item] | type_debug }}"
  loop:
    - app_name
    - app_port
    - app_debug
    - app_ratio
    - app_id
    - app_yes_no
```

🔍 **Observation** :

- `app_name` → `str` (string)
- `app_port` → `int` (entier, pas string !)
- `app_debug` → `bool`
- `app_ratio` → `float`
- `app_id` → `str` (les guillemets ont préservé "0042")
- `app_yes_no` → `str` (parce qu'on a mis des guillemets)

**Sans les guillemets** sur `app_id`, vous auriez `int 42` (perte du `00` leading) —
un classique. Sur `app_yes_no` sans guillemets, `bool True` au lieu de `str "yes"`.

## 📚 Exercice 5 — Cas réel : pourquoi ma variable n'a pas la bonne valeur ?

Reproduire un piège fréquent. Créez `vars/conflict.yml` :

```yaml
---
app_env: "from_vars_files"
```

Modifiez `lab.yml` :

```yaml
---
- name: Demo conflict vars
  hosts: web1.lab
  vars:
    app_env: "from_play_vars"
  vars_files:
    - vars/conflict.yml
  tasks:
    - name: Quelle valeur gagne ?
      ansible.builtin.debug:
        var: app_env
```

**Avant de lancer**, **devinez** : qui gagne, `from_play_vars` ou `from_vars_files` ?

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml
```

🔍 **Observation** : `from_play_vars` gagne. Pourquoi ? Parce que dans la précédence
Ansible, **`vars:` du play (niveau 14)** bat **`vars_files:` (niveau 13)**.

**Lancez maintenant avec `--extra-vars`** :

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml \
  --extra-vars "app_env=from_extra_vars"
```

🔍 **Observation** : `from_extra_vars` gagne. **Niveau 22 (`--extra-vars`)** bat tout.

C'est exactement le sujet du **lab 15 (precedence-variables)** qui couvre les 22 niveaux
en détail.

## 🔍 Observations à noter

- **`vars:`** dans le play = portée play, prio moyenne (niveau 14).
- **`vars_files:`** = idem mais en fichier externe (niveau 13, juste en dessous).
- **`--extra-vars`** = priorité absolue (niveau 22), surcharge tout.
- **YAML strict** : `yes/no` interprétés comme booléens — utiliser `true/false`.
- **Strings numériques** (IDs, numéros de version) : **toujours** entre guillemets.
- **`type_debug`** est l'outil de diagnostic n°1 quand "ma variable est bizarre".

## 🤔 Questions de réflexion

1. Vous voulez qu'un opérateur puisse forcer `app_env=prod` lors d'un run d'urgence
   sans toucher au code. Quelle approche : modifier `vars:`, ajouter un `vars_files:`,
   ou utiliser `--extra-vars` ? Pourquoi ?

2. Un collègue pose `app_port: 8080` (sans guillemets) puis utilise cette variable
   dans une commande `curl http://localhost:{{ app_port }}/health`. Pas de problème.
   Mais sur `app_id: 0042`, il lit `42` au lieu de `0042` dans son template.
   Quelle est la différence et comment l'éviter ?

3. Pourquoi `vars:` du play (niveau 14) bat-il `vars_files:` (niveau 13), alors qu'on
   pourrait imaginer le contraire (vars_files plus "officiel" car externalisé) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`include_vars:`** : charger des vars **dynamiquement** au runtime (selon une condition,
  selon un OS détecté). Différent de `vars_files:` qui est statique.
- **`set_fact:`** : créer une variable **côté managed node** pendant le play (niveau 18,
  bat le play vars). Voir lab 16.
- **`lookup('env', 'VAR')`** : lire une variable d'environnement du control node.
  Voir lab 17 (lookups).
- **Pattern `ansible_<env>.yml`** : un fichier de vars par environnement, chargé via
  `vars_files: - "vars/{{ env }}.yml"` avec `env` passé en `--extra-vars`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/variables-base/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/variables-base/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/variables-base/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
