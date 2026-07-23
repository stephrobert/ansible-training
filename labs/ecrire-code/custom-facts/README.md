# Lab 14a — Custom facts (`facts.d/*.fact`, ansible_local)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Ansible custom facts**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/custom-facts/)

The **standard facts** (`ansible_distribution`, `ansible_default_ipv4`, etc.) are collected by the **`setup`** module at the start of each play. **Custom facts** extend this mechanism: you drop a script (Bash, Python, or static JSON/INI) into **`/etc/ansible/facts.d/<name>.fact`** on the target, and Ansible reads it at each `gather_facts` and exposes the result under **`ansible_local.<name>`**.

**Use case**: tag a host with its **business role** (`web`, `db`, `cache`), expose application-specific data (deployed version, hash of the last deployment), centralize proprietary information.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Drop** a static custom fact in **INI** format into `/etc/ansible/facts.d/`.
2. **Drop** a dynamic custom fact (executable Bash script returning **JSON**).
3. **Read** a custom fact via `ansible_local.<name>` in a playbook.
4. **Filter** the `setup` output to keep only the `ansible_local`.
5. **Understand** when to use custom facts vs `set_fact` vs `host_vars`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/etc/ansible/facts.d state=absent" 2>&1 | tail -2
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab14a-custom-facts.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Target tree

```text
labs/ecrire-code/custom-facts/
├── README.md                       ← this file (guided tutorial)
└── challenge/
    ├── README.md                   ← challenge instructions
    └── tests/
        └── test_custom_facts.py    ← pytest+testinfra tests
```

The learner writes `lab.yml` and `challenge/solution.yml` themselves.

## 📚 Exercise 1 — Static INI custom fact

Create an INI file on the target. Format recognized by Ansible:

```ini
; /etc/ansible/facts.d/server.fact (on db1.lab)
[meta]
role = database
environment = production
managed_by = ansible

[deployment]
version = 1.4.2
deployed_on = 2026-04-27
```

Via Ansible (from the control node):

```yaml
---
- hosts: db1.lab
  become: true
  gather_facts: false
  tasks:
    - name: Créer /etc/ansible/facts.d/
      ansible.builtin.file:
        path: /etc/ansible/facts.d
        state: directory
        mode: "0755"

    - name: Déposer le custom fact INI
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/server.fact
        mode: "0644"
        content: |
          [meta]
          role = database
          environment = production
          managed_by = ansible

          [deployment]
          version = 1.4.2
          deployed_on = 2026-04-27
```

Run:

```bash
ansible-playbook labs/ecrire-code/custom-facts/lab.yml
```

🔍 **Observation**: **`/etc/ansible/facts.d/`** is the default path. Format `.fact`. Ansible reads the file at the next `gather_facts: true` (or ad-hoc `setup`).

## 📚 Exercise 2 — Read the custom fact

```bash
ansible db1.lab -m ansible.builtin.setup -a "filter=ansible_local"
```

Output:

```yaml
db1.lab | SUCCESS => {
    "ansible_facts": {
        "ansible_local": {
            "server": {
                "deployment": {
                    "deployed_on": "2026-04-27",
                    "version": "1.4.2"
                },
                "meta": {
                    "environment": "production",
                    "managed_by": "ansible",
                    "role": "database"
                }
            }
        },
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false
}
```

🔍 **Crucial observation**: the structure is **`ansible_local.<filename_without_.fact>.<section>.<key>`**. The filename `server.fact` produces `ansible_local.server`, the INI sections become sub-keys. **Filter `ansible_local`** isolates the custom facts.

## 📚 Exercise 3 — Use the fact in a playbook

```yaml
- hosts: db1.lab
  gather_facts: true               # ← required to collect ansible_local
  tasks:
    - name: Déposer un fichier paramétré par le custom fact
      ansible.builtin.copy:
        dest: /tmp/lab14a-custom-facts.txt
        content: |
          Hostname: {{ inventory_hostname }}
          Role: {{ ansible_local.server.meta.role }}
          Env: {{ ansible_local.server.meta.environment }}
          Deployment version: {{ ansible_local.server.deployment.version }}
        mode: "0644"
```

Output on db1.lab:

```text
Hostname: db1.lab
Role: database
Env: production
Deployment version: 1.4.2
```

🔍 **Observation**: **`gather_facts: true`** (default `true` unless disabled) is **mandatory**. Otherwise `ansible_local` is empty. To save gather time on the other facts: **`gather_subset: '!all,local'`** collects only the `ansible_local`.

## 📚 Exercise 4 — Dynamic custom fact (Bash script → JSON)

Create an executable script that returns JSON:

```bash
# /etc/ansible/facts.d/uptime.fact (mode 0755, executable)
#!/bin/bash
cat <<EOF
{
  "uptime_seconds": $(awk '{print int($1)}' /proc/uptime),
  "load_1min": "$(awk '{print $1}' /proc/loadavg)",
  "kernel": "$(uname -r)"
}
EOF
```

Via Ansible:

```yaml
- name: Déposer le custom fact dynamique
  ansible.builtin.copy:
    dest: /etc/ansible/facts.d/uptime.fact
    mode: "0755"                     # ← executable
    content: |
      #!/bin/bash
      cat <<EOF
      {
        "uptime_seconds": $(awk '{print int($1)}' /proc/uptime),
        "load_1min": "$(awk '{print $1}' /proc/loadavg)",
        "kernel": "$(uname -r)"
      }
      EOF
```

Verify:

```bash
ansible db1.lab -m ansible.builtin.setup -a "filter=ansible_local"
```

```yaml
"ansible_local": {
    "server": { ... },
    "uptime": {
        "kernel": "5.14.0-...",
        "load_1min": "0.05",
        "uptime_seconds": 3242
    }
}
```

🔍 **Observation**: Ansible **automatically detects** whether the file is executable (`+x` bit). If so, it executes it and parses the output as JSON. Enables **dynamic** facts (uptime, load, status of a local service). Alternative accepted format: YAML, INI. The script can be in Python, Perl, any language.

## 📚 Exercise 5 — Custom facts vs `set_fact` vs `host_vars`

| Mechanism | Storage | Persistence | Use case |
|-----------|---------|-------------|----------|
| **Custom fact** (`facts.d/*.fact`) | On the target | **Persistent** across runs | Business tag, role, deployed version |
| **`set_fact`** | In memory during the play | Destroyed at end of play | Intermediate computation in a playbook |
| **`host_vars/<host>.yml`** | On the control node (Git) | Versioned in the repo | Static config known in advance |
| **Dynamic inventory** | External source (Cloud, DB) | Re-collected on each run | Cloud, K8s, NetBox, dynamic infra |

🔍 **Observation**: custom facts = **truth on the target side** (the machine knows its own role). `host_vars` = **truth on the management side** (the Git repo knows). Both can coexist.

## 🔍 Observations to note

- **`/etc/ansible/facts.d/<name>.fact`** = default path.
- **Format**: INI, JSON, static YAML **OR** an executable script returning JSON/YAML.
- **Reading**: `ansible_local.<name>.<section>.<key>` after `gather_facts: true`.
- **`ansible -m setup -a "filter=ansible_local"`** isolates the custom facts.
- **Executable bit** (`mode: 0755`) → Ansible executes the script. Otherwise it reads it as static.
- **Not tested directly** on the EX294 but useful in prod.

## 🤔 Reflection questions

1. What happens if **two files** in `/etc/ansible/facts.d/` have the same section name?
2. Why place a fact script **executable in mode 0755** rather than 0644?
3. How do you **temporarily disable** the collection of custom facts? (Hint: `gather_subset: '!local'`).
4. What **security risk** comes from having an executable script in `facts.d/` writable by a non-root user?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): drop an INI custom fact **and** a Bash script custom fact, read both in a playbook that drops a proof file.

## 💡 Going further

- **Custom path**: `/etc/ansible/facts.d/` is the default. Change it with `ansible.builtin.setup -a "fact_path=/custom/path"`.
- **Caching**: combine custom facts + `fact_caching = jsonfile` in `ansible.cfg` to avoid re-collecting on each run.
- **Module `set_fact: cacheable: true`**: alternative to persist a fact on the cache side (not the target side).
- **Lab 14**: standard facts and magic vars (prerequisite).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/ecrire-code/custom-facts/lab.yml
ansible-lint --profile production labs/ecrire-code/custom-facts/challenge/solution.yml
```
