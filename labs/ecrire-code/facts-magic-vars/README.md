# Lab 14 — Facts and magic vars (`ansible_facts`, `hostvars`)

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

🔗 [**Ansible facts and magic vars: ansible_facts, gather_subset, hostvars**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/facts-magic-vars/)

**Facts** are system information collected automatically by Ansible
at the start of a play (`gather_facts: true` by default): OS, version, IP, memory,
CPU, network interfaces, etc. **Magic vars** are variables provided by
Ansible (not by the managed nodes): `inventory_hostname`, `groups`, `hostvars`,
`play_hosts`, `ansible_play_batch`, `ansible_play_hosts_all`. Mastering these two
categories lets you **make your playbooks dynamic** and **multi-host** without
hardcoding values.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Read** the most useful system facts (`ansible_distribution`, `ansible_default_ipv4`).
2. **Use** the magic vars (`inventory_hostname`, `groups`, `hostvars`).
3. **Access** another host's facts via `hostvars['<hostname>']`.
4. **Limit** the collection with `gather_subset:` to gain performance.
5. **Disable** `gather_facts:` when the facts are not needed.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ping
```

## 📚 Exercise 1 — See all the facts (curiosity)

Run `setup` ad-hoc to explore:

```bash
ansible web1.lab -m ansible.builtin.setup | less
```

🔍 **Observation**: huge output! Each managed node returns **300-500 facts**.
The most useful:

- `ansible_distribution`, `ansible_distribution_version` (`AlmaLinux`, `10.1`)
- `ansible_default_ipv4.address` (`10.10.20.21`)
- `ansible_memtotal_mb` (total memory in MB)
- `ansible_processor_count` / `ansible_processor_vcpus` (CPU)
- `ansible_hostname` / `ansible_fqdn` (short hostname / FQDN)
- `ansible_kernel`, `ansible_architecture`
- `ansible_interfaces` (list of network interfaces)

**Filter** a specific fact:

```bash
ansible web1.lab -m ansible.builtin.setup -a "filter=ansible_default_ipv4"
```

## 📚 Exercise 2 — Read the facts in a play

Create `lab.yml`:

```yaml
---
- name: Demo facts systeme
  hosts: web1.lab
  become: true
  tasks:
    - name: Afficher les facts cles
      ansible.builtin.debug:
        msg: |
          host : {{ inventory_hostname }}
          fqdn : {{ ansible_fqdn }}
          os : {{ ansible_distribution }} {{ ansible_distribution_version }}
          kernel : {{ ansible_kernel }}
          memoire : {{ ansible_memtotal_mb }} MB
          cpu : {{ ansible_processor_vcpus }} vCPU
          ipv4 : {{ ansible_default_ipv4.address }}
          interfaces : {{ ansible_interfaces | join(', ') }}
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation**: all the facts are available **without `vars:`**: Ansible collected
them at the start of the play (`gather_facts: true` is implicit by default).

## 📚 Exercise 3 — Magic vars (`inventory_hostname`, `groups`, `hostvars`)

Modify `lab.yml` to use the magic vars:

```yaml
- name: Demo magic vars
  hosts: webservers
  tasks:
    - name: Afficher les magic vars
      ansible.builtin.debug:
        msg: |
          mon hostname (inventaire) : {{ inventory_hostname }}
          mon hostname (managed node) : {{ ansible_hostname }}
          membres du groupe webservers : {{ groups['webservers'] }}
          tous les hosts du play : {{ ansible_play_hosts_all }}
          batch courant : {{ ansible_play_batch }}
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation**:

- **`inventory_hostname`** = the name **in the inventory** (what Ansible sees). It is
  always **`web1.lab`** here, regardless of the VM's real hostname.
- **`ansible_hostname`** = the name **reported by the VM** (`hostname -s`). It can be
  different (renamed machine, different FQDN, etc.).
- **`groups['webservers']`** = list of the group's members.
- **`ansible_play_hosts_all`** = all the hosts of the play (even those that failed).
- **`ansible_play_batch`** = hosts of the **current batch** (useful with `serial:`).

## 📚 Exercise 4 — `hostvars`: access another host's facts

```yaml
- name: Demo hostvars
  hosts: web1.lab
  become: true
  tasks:
    - name: Afficher des facts d autres hotes
      ansible.builtin.debug:
        msg: |
          IP de web2 : {{ hostvars['web2.lab'].ansible_default_ipv4.address | default('inconnu') }}
          OS de db1 : {{ hostvars['db1.lab'].ansible_distribution | default('inconnu') }}
```

**Run first**:

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation**: depending on whether web2 and db1 have already been "fact-gathered"
in this session, you get either the real values or `inconnu` (the `default` filter).

**Why**? `hostvars` only contains facts if Ansible **has contacted** those
hosts. In the play `hosts: web1.lab`, Ansible only gathers web1's facts.

**Solution**: pre-collect the facts by running a first `hosts: all` play.

```yaml
---
- name: Pre-gather facts pour tout le lab
  hosts: all
  gather_facts: true
  tasks: []

- name: Vrai play qui utilise les facts d autres hotes
  hosts: web1.lab
  tasks:
    - name: Afficher l IP de web2 (maintenant disponible)
      ansible.builtin.debug:
        msg: "IP de web2 : {{ hostvars['web2.lab'].ansible_default_ipv4.address }}"
```

## 📚 Exercise 5 — `gather_subset:` to limit the collection

On 100 hosts, the full `gather_facts: true` takes **30+ seconds**. Often, you
only need a fraction.

```yaml
---
- name: Demo gather_subset minimaliste
  hosts: web1.lab
  gather_facts: true
  gather_subset:
    - "!all"        # Do not collect everything
    - "!min"        # Not even the minimum
    - network       # But collect network
  tasks:
    - name: Verifier ce qui est collecte
      ansible.builtin.debug:
        msg: |
          IP : {{ ansible_default_ipv4.address | default('non collecte') }}
          OS : {{ ansible_distribution | default('non collecte') }}
          memoire : {{ ansible_memtotal_mb | default('non collecte') }}
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/lab.yml
```

🔍 **Observation**:

- `ansible_default_ipv4.address` is available (`network` subset collected).
- `ansible_distribution` and `ansible_memtotal_mb` may be **absent** if not
  included.

**Available subsets**: `all`, `min`, `network`, `hardware`, `virtual`, `facter`,
`ohai`. The `!` prefix excludes.

## 📚 Exercise 6 — Disable `gather_facts` entirely

When you **need no fact at all** (just copying a file, for example),
`gather_facts: false` saves 1-3s per host:

```yaml
---
- name: Play sans facts
  hosts: web1.lab
  gather_facts: false
  tasks:
    - name: Tester un fact (devrait planter)
      ansible.builtin.debug:
        msg: "OS : {{ ansible_distribution | default('non collecte') }}"

    - name: Mais inventory_hostname marche
      ansible.builtin.debug:
        msg: "host inventaire : {{ inventory_hostname }}"
```

🔍 **Observation**:

- `ansible_distribution` is `non collecte` (default filter).
- `inventory_hostname` **always** works: it is an Ansible magic var, not a fact.

## 🔍 Observations to note

- **Facts** = collected on the managed node (`gather_facts: true`).
- **Magic vars** = provided by Ansible (`inventory_hostname`, `groups`, `hostvars`).
- **`inventory_hostname`** ≠ **`ansible_hostname`** (inventory name vs real VM name).
- **`hostvars`** only contains the hosts **already contacted** in this session.
- **`gather_subset:`** + **`gather_facts: false`** = **performance** levers on large fleets.
- **Pre-collect the facts** in a `hosts: all` play before a multi-host play.

## 🤔 Reflection questions

1. You want to generate a complete `/etc/hosts` file on web1, containing the IPs
   of **all** the managed nodes. Which pattern do you use (combination of `groups`,
   `hostvars`, `loop:`)?

2. `ansible_fqdn` returns `web1.lab` on web1, but `ansible_hostname` returns just
   `web1`. What is the internal difference (what is queried on the managed
   node)?

3. On 200 hosts, `gather_facts: true` takes 1 minute. You only need the IPs
   and the OS. What do you put in `gather_subset:` to save time?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`fact_caching`**: configure `ansible.cfg` with `fact_caching = jsonfile` to
  **persist the facts** across runs. Avoids re-collecting on unchanged hosts.
- **`ansible_local`**: custom facts dropped into `/etc/ansible/facts.d/*.fact` on the
  managed node side. Read automatically and exposed under `ansible_local.<filename>.<key>`.
- **`set_fact:`** + **`cacheable: true`**: create a dynamic fact at runtime and
  persist it in the cache. See lab 16.
- **`inventory_hostname_short` pattern**: magic var that gives just `web1` instead
  of `web1.lab`: useful when the inventory uses FQDNs but your templates
  want the short name.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/facts-magic-vars/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/facts-magic-vars/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/facts-magic-vars/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
