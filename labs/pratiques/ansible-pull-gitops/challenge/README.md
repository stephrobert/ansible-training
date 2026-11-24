# Four hundred nodes your control node will never reach

## The situation

The new fleet lives in shops behind consumer routers: no public address, no
inbound SSH, sometimes offline for a day. Your control node cannot reach any of
them, and the push model has run out of road. There is no more central machine
opening connections outward. If a node wants its configuration, it will have to
go and get it, from the one thing it can always reach: a Git repository.

Your mission, from the project directory:

1. Publish the configuration as a **Git repository** and have the target pull it
   and apply it **to itself**, no control node in the loop.
2. Prove it ran by having the pulled play leave evidence on the node it was
   executed from, not on the machine that wrote the playbook.
3. Make it **autonomous**: schedule the pull so the node converges on its own, and
   arrange for a freshly provisioned machine to bootstrap itself on first boot.
4. Draw the line for your team: what push still does better, what pull buys you at
   the edge or at four hundred nodes, and what you give up in exchange.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/ansible-pull-gitops/ (in French)

## 🎯 Challenge — Run `ansible-pull` from db1.lab

### ✅ Objective

Make **db1.lab configure itself** in pull mode: a
Git repo containing a `pull-playbook.yml`, cloned and run on db1 by
**`ansible-pull`**. No pre-shipped demo: you are the one who creates the repo,
the playbook and the orchestration script.

The tests do not read your files: they run your script then
check **the state of db1.lab**.

| Expected state on db1.lab | Proof |
| --- | --- |
| `/var/lib/ansible-pull/` is a Git clone containing `pull-playbook.yml` | `ansible-pull` did clone (nobody copied the marker by hand) |
| `/tmp/lab98-pull-marker.txt` exists, owner `root`, mode `0644` | the pulled playbook ran with privileges |
| The marker contains `ansible-pull executed` and the machine's hostname | the play ran **on db1**, not on the control node |

### 🧩 Steps (you write the content)

#### Step 1 — The local Git repo

Create `repo-pull/` in this lab, write `pull-playbook.yml` in it, then make
it a real repo (`git init` + commit). The playbook targets the machine that
runs it, not a remote host:

```yaml
---
- hosts: ???                   # the target runs itself
  connection: ???
  become: true
  gather_facts: true
  tasks:
    - name: Marker pull executed
      ansible.builtin.copy:
        dest: ???
        content: |
          ansible-pull executed at: {{ ??? }}
          hostname: {{ ??? }}
        owner: ???
        group: ???
        mode: ???
```

#### Step 2 — The orchestrator script `challenge/solution.sh`

A shell script (not a playbook) that, in order:

1. Installs `ansible-core` and `git` on db1.lab (the only push of the lab:
   the bootstrap). Tip: `ansible db1.lab -b -m ansible.builtin.dnf -a ...`
   resolves the IP through the inventory, unlike a direct `ssh db1.lab`.
2. Transfers `repo-pull/` to db1 (for example under `/tmp/lab98-repo-pull`).
   Warning: the `.git/` must survive the transfer, otherwise `ansible-pull`
   cannot clone. A `tar` archive is your friend. In production, it
   would be an `https://` URL and this step would not exist.
3. Runs `ansible-pull` **on db1** (via `ansible -b -m ansible.builtin.command`)
   with `-U <repo-path-on-db1>`, `-d /var/lib/ansible-pull` and the name
   of the playbook.

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 1. bootstrap: tooling on the target
ansible db1.lab -b -m ansible.builtin.dnf -a "???"

# 2. transfer the repo (preserve .git/)
???

# 3. the target pulls and applies its config
ansible db1.lab -b -m ansible.builtin.command \
  -a "ansible-pull -U ??? -d ??? ???"
```

> 💡 **Traps**:
>
> - **`hosts: localhost` + `connection: local`** in `pull-playbook.yml`:
>   it is the target itself that runs. A `hosts: db1.lab` would match
>   nothing in `ansible-pull`'s default inventory.
> - **`ansible-pull` clones via git**: the path passed to `-U` must be a
>   valid Git repo **seen from db1** (local folder on db1 or URL).
> - **Owner `root`**: `ansible-pull` must run with elevation (`-b` on
>   the ad-hoc command), otherwise the marker will belong to `ansible`.

### 🚀 Run

```bash
chmod +x labs/pratiques/ansible-pull-gitops/challenge/solution.sh
bash labs/pratiques/ansible-pull-gitops/challenge/solution.sh
```

### 🧪 Automated validation

```bash
pytest -v labs/pratiques/ansible-pull-gitops/challenge/tests/
```

The tests reset db1, run your `solution.sh`, then
check on db1 the Git clone and the marker (owner, mode, content).

### 🧹 Reset

```bash
dsoxlab clean pratiques-ansible-pull-gitops
```

### 💡 Going further

- **Periodic run**: set up a cron or a systemd timer that re-runs
  `ansible-pull` every 30 minutes: the node converges on its own.
- **Cloud-init**: integrate `ansible-pull` into `runcmd:` for an immutable
  bootstrap on first boot.
- **AAP Tower**: does NOT support pull. If you target AAP, stay in push.
