# Lab 27 — Filtres Jinja2 avancés (`regex`, `b64`, `password_hash`, `json_query`)

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

🔗 [**Filtres Jinja2 avancés Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/filtres-jinja/)

Au-delà des **filtres essentiels** vus au lab 19 (`default`, `combine`, `selectattr`,
`map`), Ansible expose des **filtres avancés** pour des cas spécialisés :

- **`regex_search` / `regex_findall` / `regex_replace`** : extraction et
  substitution par regex.
- **`b64encode` / `b64decode`** : encodage base64 (pour headers HTTP, secrets
  Kubernetes).
- **`hash` / `password_hash`** : hachage (SHA, MD5, bcrypt).
- **`json_query`** : extractions complexes type `jq`.
- **`ipaddr`** (collection ansible.utils) : manipulation d'IPs et CIDR.

Ces filtres sont les outils qui permettent de **se passer de scripts Python externes**
dans des cas non triviaux.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Extraire** une partie d'une string avec `regex_search`.
2. **Encoder** un secret en base64 pour un manifest Kubernetes ou un header.
3. **Hacher** un mot de passe utilisateur (`password_hash('sha512')`).
4. **Filtrer** un JSON complexe avec `json_query` (syntaxe JMESPath).
5. **Manipuler** des IPs et CIDR avec `ipaddr`.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
ansible-galaxy collection install community.general ansible.utils
```

## 📚 Exercice 1 — `regex_search` : extraire une partie d'une string

```yaml
---
- name: Demo regex_search
  hosts: db1.lab
  tasks:
    - name: Extraire la version major depuis ansible_distribution_version
      ansible.builtin.debug:
        msg: "Major : {{ ansible_distribution_version | regex_search('^(\\d+)\\.', '\\1') | first }}"

    - name: Extraire l IP depuis une string libre
      vars:
        log_line: "Connection from 192.168.1.42 on port 22"
      ansible.builtin.debug:
        msg: "IP detectee : {{ log_line | regex_search('\\d+\\.\\d+\\.\\d+\\.\\d+') }}"

    - name: Extraire toutes les IPs d un texte
      vars:
        log_text: "Source 10.0.0.1 dest 192.168.1.42 then 172.16.0.5"
      ansible.builtin.debug:
        msg: "IPs : {{ log_text | regex_findall('\\d+\\.\\d+\\.\\d+\\.\\d+') }}"
```

🔍 **Observation** :

- `regex_search('pattern')` → retourne la **première** occurrence ou `None`.
- `regex_search('(group)', '\\1')` → retourne le **groupe capturé**.
- `regex_findall('pattern')` → retourne **toutes les occurrences** en liste.

**Échappement** : dans YAML, `\\d` (double backslash) car YAML mange un `\`. En
Python pur ce serait `\d`.

## 📚 Exercice 2 — `regex_replace` : substitution

```yaml
- name: Demo regex_replace
  vars:
    fqdn: "web1.lab.example.com"
  block:
    - name: Extraire le hostname court
      ansible.builtin.debug:
        msg: "{{ fqdn | regex_replace('\\..*$', '') }}"
        # → web1

    - name: Remplacer le domaine
      ansible.builtin.debug:
        msg: "{{ fqdn | regex_replace('\\.[^.]+\\.[^.]+$', '.prod.example.com') }}"
        # → web1.lab.prod.example.com → en fait → web1.prod.example.com
```

🔍 **Observation** : `regex_replace('pattern', 'remplacement')` substitue **toutes**
les occurrences (équivalent `re.sub` Python). Pour ne remplacer que la première,
utiliser un pattern plus précis.

## 📚 Exercice 3 — `b64encode` / `b64decode`

```yaml
- name: Demo base64
  vars:
    secret: "p@ssw0rd-very-secret-2026"
  block:
    - name: Encoder
      ansible.builtin.debug:
        msg: "{{ secret | b64encode }}"
        # → cEBzc3cwcmQtdmVyeS1zZWNyZXQtMjAyNg==

    - name: Decoder
      ansible.builtin.debug:
        msg: "{{ 'cEBzc3cwcmQtdmVyeS1zZWNyZXQtMjAyNg==' | b64decode }}"
        # → p@ssw0rd-very-secret-2026
```

**Cas d'usage** :

```yaml
- name: Generer un manifest Kubernetes Secret
  ansible.builtin.copy:
    content: |
      apiVersion: v1
      kind: Secret
      metadata:
        name: db-credentials
      type: Opaque
      data:
        password: {{ secret | b64encode }}
    dest: /tmp/secret.yml
```

🔍 **Observation** : Kubernetes attend les valeurs de `data:` en **base64**. Sans
`b64encode`, vous mettez le password en clair (déclaré "encodé" mais en fait pas).

## 📚 Exercice 4 — `password_hash` (hachage password)

```yaml
- name: Demo password_hash
  vars:
    plain_password: "MotDePasseUtilisateur"
  block:
    - name: Hash SHA-512 (compatible /etc/shadow)
      ansible.builtin.debug:
        msg: "{{ plain_password | password_hash('sha512') }}"
        # → $6$randomsalt$hashvalue...

    - name: Hash bcrypt (pour des apps modernes)
      ansible.builtin.debug:
        msg: "{{ plain_password | password_hash('bcrypt') }}"

    - name: Hash deterministique (avec salt fixe — pour idempotence)
      ansible.builtin.debug:
        msg: "{{ plain_password | password_hash('sha512', 'mysalt') }}"
```

🔍 **Observation** :

- **`password_hash('sha512')`** est compatible avec `/etc/shadow` — utilisé par
  `ansible.builtin.user: password:`.
- **Sans salt**, chaque appel génère un hash différent (sécurité). Mais perte
  d'**idempotence** : la tâche `user:` rapporte `changed` à chaque run.
- **Avec salt fixe**, hash déterministe → idempotence garantie. **Mais** salt fixe
  est un anti-pattern sécurité — préférer **stocker le hash** dans `host_vars/`
  (avec Vault) plutôt que regénérer à chaque run.

```yaml
# Pattern propre : hash genere une fois, stocke dans host_vars (vault)
- ansible.builtin.user:
    name: alice
    password: "{{ alice_password_hash }}"  # hash deja stocke
```

## 📚 Exercice 5 — `json_query` (équivalent `jq`)

`json_query` permet de naviguer dans des structures JSON complexes avec la syntaxe
**JMESPath**.

```yaml
- name: Demo json_query
  vars:
    response:
      items:
        - { id: 1, name: alice, roles: [admin, dev] }
        - { id: 2, name: bob, roles: [dev] }
        - { id: 3, name: charlie, roles: [admin] }
        - { id: 4, name: dave, roles: [readonly] }
  block:
    - name: Extraire les noms des admins
      ansible.builtin.debug:
        msg: "{{ response | community.general.json_query(\"items[?contains(roles, 'admin')].name\") }}"
        # → [alice, charlie]

    - name: Extraire les ids et noms (projection)
      ansible.builtin.debug:
        msg: "{{ response | community.general.json_query('items[*].{id: id, name: name}') }}"
```

🔍 **Observation** : JMESPath est puissant mais **syntaxe spécifique**.
`items[?contains(roles, 'admin')].name` = "depuis items, garde ceux où roles contient
admin, projette sur name". Cas d'usage : **parser la sortie d'une API** (`uri:`)
qui retourne du JSON nested.

**Alternative pure-Jinja** : `selectattr('roles', 'contains', 'admin') |
map(attribute='name')` — souvent plus lisible que JMESPath sur les cas simples.

## 📚 Exercice 6 — `ipaddr` (manipulation d'IPs et CIDR)

```yaml
- name: Demo ipaddr (collection ansible.utils)
  vars:
    network: "192.168.1.0/24"
  block:
    - name: Premiere IP utilisable
      ansible.builtin.debug:
        msg: "{{ network | ansible.utils.ipaddr('first_usable') }}"
        # → 192.168.1.1

    - name: Derniere IP utilisable
      ansible.builtin.debug:
        msg: "{{ network | ansible.utils.ipaddr('last_usable') }}"
        # → 192.168.1.254

    - name: Nombre d adresses
      ansible.builtin.debug:
        msg: "{{ network | ansible.utils.ipaddr('size') }}"
        # → 256

    - name: Verifier si une IP est dans le subnet
      ansible.builtin.debug:
        msg: "192.168.1.42 dans {{ network }} : {{ '192.168.1.42' | ansible.utils.ipaddr(network) }}"

    - name: Reseau /16 a partir d une IP /24
      ansible.builtin.debug:
        msg: "{{ network | ansible.utils.ipaddr('network/16') }}"
```

🔍 **Observation** : `ipaddr` couvre 90% des manipulations IP : extraire le réseau
parent, compter les hôtes, valider qu'une IP est dans un range. Très utile pour
des configs réseau dynamiques.

## 📚 Exercice 7 — Le piège : filtres qui ne sont **pas dans builtin**

`json_query` est dans **`community.general`**, pas dans `ansible.builtin`. Sans
la collection installée, vous obtenez une erreur cryptique.

```bash
ansible-galaxy collection install community.general ansible.utils
```

🔍 **Observation** : sur Ansible Core 2.20, `community.general` et `ansible.utils`
**ne sont pas inclus par défaut**. Il faut les installer via `ansible-galaxy`.

**Convention** : préfixer **toujours** le nom du filtre avec le namespace si la
collection n'est pas builtin :

```yaml
{{ var | community.general.json_query('items[*].id') }}
{{ network | ansible.utils.ipaddr('network/24') }}
```

## 🔍 Observations à noter

- **`regex_search('pattern', '\\1')`** = extraction par regex avec capture de groupe.
- **`b64encode`** / **`b64decode`** = pour secrets Kubernetes, headers HTTP.
- **`password_hash('sha512')`** = hash compatible `/etc/shadow` — penser au **salt fixe** pour idempotence.
- **`json_query`** (community.general) = JMESPath pour navigation JSON complexe.
- **`ipaddr`** (ansible.utils) = manipulation IPs / CIDR.
- **Filtres hors builtin** nécessitent `ansible-galaxy collection install`.

## 🤔 Questions de réflexion

1. Vous voulez générer un manifest Kubernetes `Secret` à partir de variables
   `username` et `password`. Quel pipeline de filtres ?

2. `password_hash('sha512')` génère un hash différent à chaque run sans salt fixe.
   Pourquoi est-ce un problème **idempotence** sur le module `user:` ? Quelle
   est la solution propre ?

3. Vous parsez un JSON volumineux (sortie d'une API REST). Quand préférer
   `json_query` (JMESPath) vs `selectattr + map` (pure Jinja2) ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`hash('sha256')`** : simple hash (pas adapté aux passwords — utiliser
  `password_hash` qui ajoute le salt automatiquement).
- **`urlencode`** / **`urldecode`** : encodage URL pour des params HTTP.
- **`from_yaml` / `to_yaml`** : conversion entre string YAML et structure native —
  utile pour parser une config retournée par un `command:`.
- **`win_url_encode`** (Windows-specific, dans community.windows) — pour les
  scenarios Windows / IIS.
- **Plugin filter custom** : on peut écrire son propre filtre Python dans
  `plugins/filter/mes_filtres.py` au niveau du repo. À utiliser avec parcimonie —
  préférer les filtres officiels.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/filtres-jinja-avances/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
