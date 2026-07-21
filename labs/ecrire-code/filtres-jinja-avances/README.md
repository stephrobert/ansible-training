# Lab 27 — Advanced Jinja2 filters (`regex`, `b64`, `password_hash`, `json_query`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**Advanced Jinja2 filters in Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/filtres-jinja/)

Beyond the **essential filters** seen in lab 19 (`default`, `combine`, `selectattr`,
`map`), Ansible exposes **advanced filters** for specialized cases:

- **`regex_search` / `regex_findall` / `regex_replace`**: extraction and
  substitution by regex.
- **`b64encode` / `b64decode`**: base64 encoding (for HTTP headers, Kubernetes
  secrets).
- **`hash` / `password_hash`**: hashing (SHA, MD5, bcrypt).
- **`json_query`**: complex `jq`-style extractions.
- **`ipaddr`** (ansible.utils collection): manipulation of IPs and CIDR.

These filters are the tools that let you **avoid external Python scripts**
in non-trivial cases.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Extract** part of a string with `regex_search`.
2. **Encode** a secret in base64 for a Kubernetes manifest or a header.
3. **Hash** a user password (`password_hash('sha512')`).
4. **Filter** complex JSON with `json_query` (JMESPath syntax).
5. **Manipulate** IPs and CIDR with `ipaddr`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible-galaxy collection install community.general ansible.utils
```

## 📚 Exercise 1 — `regex_search`: extract part of a string

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

🔍 **Observation**:

- `regex_search('pattern')` → returns the **first** occurrence or `None`.
- `regex_search('(group)', '\\1')` → returns the **captured group**.
- `regex_findall('pattern')` → returns **all occurrences** as a list.

**Escaping**: in YAML, `\\d` (double backslash) because YAML eats one `\`. In
pure Python it would be `\d`.

## 📚 Exercise 2 — `regex_replace`: substitution

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
        # → web1.lab.prod.example.com → actually → web1.prod.example.com
```

🔍 **Observation**: `regex_replace('pattern', 'replacement')` substitutes **all**
occurrences (equivalent to Python's `re.sub`). To replace only the first one,
use a more precise pattern.

## 📚 Exercise 3 — `b64encode` / `b64decode`

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

**Use case**:

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

🔍 **Observation**: Kubernetes expects the `data:` values in **base64**. Without
`b64encode`, you put the password in plaintext (declared "encoded" but actually not).

## 📚 Exercise 4 — `password_hash` (password hashing)

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

🔍 **Observation**:

- **`password_hash('sha512')`** is compatible with `/etc/shadow`, used by
  `ansible.builtin.user: password:`.
- **Without a salt**, each call generates a different hash (security). But loss
  of **idempotence**: the `user:` task reports `changed` on every run.
- **With a fixed salt**, a deterministic hash → guaranteed idempotence. **But** a
  fixed salt is a security anti-pattern: prefer to **store the hash** in `host_vars/`
  (with Vault) rather than regenerate it on every run.

```yaml
# Clean pattern: hash generated once, stored in host_vars (vault)
- ansible.builtin.user:
    name: alice
    password: "{{ alice_password_hash }}"  # hash already stored
```

## 📚 Exercise 5 — `json_query` (equivalent to `jq`)

`json_query` lets you navigate complex JSON structures with the **JMESPath**
syntax.

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

🔍 **Observation**: JMESPath is powerful but has a **specific syntax**.
`items[?contains(roles, 'admin')].name` = "from items, keep those where roles
contains admin, project onto name". Use case: **parse the output of an API** (`uri:`)
that returns nested JSON.

**Pure-Jinja alternative**: `selectattr('roles', 'contains', 'admin') |
map(attribute='name')`, often more readable than JMESPath in simple cases.

## 📚 Exercise 6 — `ipaddr` (manipulation of IPs and CIDR)

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

🔍 **Observation**: `ipaddr` covers 90% of IP manipulations: extract the parent
network, count the hosts, validate that an IP is in a range. Very useful for
dynamic network configs.

## 📚 Exercise 7 — The pitfall: filters that are **not in builtin**

`json_query` is in **`community.general`**, not in `ansible.builtin`. Without
the collection installed, you get a cryptic error.

```bash
ansible-galaxy collection install community.general ansible.utils
```

🔍 **Observation**: on Ansible Core 2.20, `community.general` and `ansible.utils`
**are not included by default**. You must install them via `ansible-galaxy`.

**Convention**: **always** prefix the filter name with the namespace if the
collection is not builtin:

```yaml
{{ var | community.general.json_query('items[*].id') }}
{{ network | ansible.utils.ipaddr('network/24') }}
```

## 🔍 Observations to note

- **`regex_search('pattern', '\\1')`** = regex extraction with group capture.
- **`b64encode`** / **`b64decode`** = for Kubernetes secrets, HTTP headers.
- **`password_hash('sha512')`** = hash compatible with `/etc/shadow`; think of a **fixed salt** for idempotence.
- **`json_query`** (community.general) = JMESPath for complex JSON navigation.
- **`ipaddr`** (ansible.utils) = IPs / CIDR manipulation.
- **Non-builtin filters** require `ansible-galaxy collection install`.

## 🤔 Reflection questions

1. You want to generate a Kubernetes `Secret` manifest from `username`
   and `password` variables. What filter pipeline?

2. `password_hash('sha512')` generates a different hash on every run without a
   fixed salt. Why is this an **idempotence** problem on the `user:` module? What
   is the clean solution?

3. You parse a large JSON (output of a REST API). When should you prefer
   `json_query` (JMESPath) vs `selectattr + map` (pure Jinja2)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`hash('sha256')`**: simple hash (not suited to passwords; use
  `password_hash`, which adds the salt automatically).
- **`urlencode`** / **`urldecode`**: URL encoding for HTTP params.
- **`from_yaml` / `to_yaml`**: conversion between a YAML string and a native
  structure, useful to parse a config returned by a `command:`.
- **`win_url_encode`** (Windows-specific, in community.windows): for Windows / IIS
  scenarios.
- **Custom filter plugin**: you can write your own Python filter in
  `plugins/filter/mes_filtres.py` at the repo level. Use it sparingly; prefer the
  official filters.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/filtres-jinja-avances/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/filtres-jinja-avances/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
