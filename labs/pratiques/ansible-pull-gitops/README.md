# Lab 98 — `ansible-pull`: GitOps / Edge pattern (outside RHCE EX294)

> ⚠️ **Outside RHCE EX294**: this lab covers a pattern useful in modern
> production (Edge, GitOps, IoT) but **not tested** at the RHCE 2026 exam.
> Look at it after mastering the classic SSH push basics.

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```

## 🧠 Recap

🔗 [**Pull mode with ansible-pull (GitOps Edge)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/ansible-pull-gitops/)

Ansible works by default in **push** mode: a control node SSHes to the targets. But there is a **pull** mode: the target **fetches its playbook from a Git repo** (with **`ansible-pull`**) and **runs itself**. No need for a centralized control node. No need for reverse SSH access.

**2026 use cases**:

- **Edge computing / IoT**: nodes isolated behind a NAT, without a public IP, that pull their config.
- **Immutable bootstrap**: integration into **cloud-init** so that a provisioned VM configures itself on first boot.
- **Massive scaling (>1000 nodes)**: avoid the control node bottleneck.
- **GitOps pattern**: the **Git branch** is the source of truth, each node reflects the state of the repo.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Understand** the difference between push and pull (who initiates the connection).
2. **Run** `ansible-pull` manually against a public Git repo.
3. **Configure** a periodic run via **`cron`** or a **systemd timer**.
4. **Integrate** `ansible-pull` into **`cloud-init`** for boot bootstrap.
5. **Understand** the **limits**: no centralized logs, no control node, no AAP Tower.
6. **Choose** push vs pull depending on the use case.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible-pull --version
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab98-pull-marker.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Target tree

```text
labs/pratiques/ansible-pull-gitops/
├── README.md                       ← this file (guided tutorial)
├── repo-pull/                      ← (to create) fake local Git repo
│   ├── pull-playbook.yml
│   └── README.md
└── challenge/
    ├── README.md                   ← challenge brief
    └── tests/
        └── test_pull.py            ← structural tests
```

The learner writes the `pull-playbook.yml` + `challenge/solution.sh` themselves (script that orchestrates `ansible-pull`).

## 📚 Exercise 1 — Push vs Pull

| Criterion | **push** mode (default) | **pull** mode (`ansible-pull`) |
|---------|-------------------------|-------------------------------|
| Who initiates the connection? | Control node → targets (SSH) | Target → Git repo (HTTPS/SSH) |
| Centralization | Yes (control node) | No (each node autonomous) |
| Log visibility | Centralized | Distributed (each node locally) |
| Typical use case | Datacenter, managed fleet | Edge, IoT, NAT, bootstrap |
| Compatible with AAP Tower | Yes | No (pure ansible-core mode) |
| Supports FQCN, collections, vault | Yes | Yes |

🔍 **Observation**: `ansible-pull` **uses the same playbooks** as `ansible-playbook`. The **difference is just who runs it**, not the content of the playbook. Lets you **switch** a project from push to pull without rewriting.

## 📚 Exercise 2 — Minimal `ansible-pull`

On **db1.lab** (the target runs it itself):

```bash
sudo dnf install -y ansible-core git

# Run ansible-pull against a public Git repo
ansible-pull \
  -U https://github.com/stephrobert/ansible-pull-demo.git \
  -d /var/lib/ansible-pull \
  pull-playbook.yml
```

What `ansible-pull` does:

1. `git clone` (or `git pull` if already cloned) the repo into `/var/lib/ansible-pull/`.
2. `ansible-playbook` on **`pull-playbook.yml`** with `hosts: localhost` (by default).
3. Exits with the return code of the playbook.

🔍 **Observation**: `-U <git-url>` is the mandatory argument. **`-d <path>`** locates the clone (default `/var/lib/ansible/local`). **`pull-playbook.yml`** is the name of the playbook inside the repo (default `local.yml`).

## 📚 Exercise 3 — Local Git repo for the lab

Since we do not have a remote Git repo for the lab, we simulate with a **local folder**:

```bash
# Create a fake local "repo" (in practice: a Git repo with a push origin)
mkdir -p labs/pratiques/ansible-pull-gitops/repo-pull
cat > labs/pratiques/ansible-pull-gitops/repo-pull/pull-playbook.yml <<'EOF'
---
- hosts: localhost
  connection: local
  become: true
  # true: the marker below reads facts. Setting gather_facts to false would
  # leave ansible_date_time and ansible_hostname undefined, and a default()
  # would quietly write "unknown"/"localhost" instead of failing.
  gather_facts: true
  tasks:
    - name: Marker pull executed
      ansible.builtin.copy:
        dest: /tmp/lab98-pull-marker.txt
        content: |
          ansible-pull executed at: {{ ansible_date_time.iso8601 }}
          hostname: {{ ansible_hostname }}
        owner: root
        group: root
        mode: "0644"
EOF

cd labs/pratiques/ansible-pull-gitops/repo-pull/
git init && git add . && git -c user.email=a@b -c user.name=lab commit -m "initial"
```

Run `ansible-pull` with this local source (from db1.lab):

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab "
  sudo dnf install -y ansible-core git
  sudo ansible-pull -U $ANSIBLE_TRAINING/labs/pratiques/ansible-pull-gitops/repo-pull \
    -d /var/lib/ansible-pull \
    pull-playbook.yml
"
```

🔍 **Observation**: for the demo we use a local path. In prod, it is **`https://github.com/...`** or **`git@gitlab.com:...`** with an **SSH key deployed** on the node (typically via cloud-init).

## 📚 Exercise 4 — Periodic run via cron

Common pattern: cron every 30 minutes to synchronize with the repo.

```cron
# /etc/cron.d/ansible-pull
*/30 * * * * root /usr/bin/ansible-pull \
  -U https://github.com/myorg/infra.git \
  -d /var/lib/ansible-pull \
  pull-playbook.yml \
  >> /var/log/ansible-pull.log 2>&1
```

Via Ansible (initial push that configures the pull):

```yaml
- name: Configurer ansible-pull en cron
  ansible.builtin.cron:
    name: ansible-pull
    user: root
    minute: "*/30"
    job: >-
      /usr/bin/ansible-pull
      -U https://github.com/myorg/infra.git
      -d /var/lib/ansible-pull
      pull-playbook.yml
      >> /var/log/ansible-pull.log 2>&1
```

🔍 **Observation**: **bootstrap then pull** pattern: (1) initial push to install ansible-core + drop the cron, (2) then the node **self-configures** from the repo. The agent stays minimal.

## 📚 Exercise 5 — cloud-init integration

```yaml
# user-data cloud-init
#cloud-config
packages:
  - ansible-core
  - git

runcmd:
  - ansible-pull -U https://github.com/myorg/infra.git pull-playbook.yml
```

🔍 **Observation**: **immutable / Edge** pattern. A new VM **boots** with cloud-init → `ansible-pull` runs the playbook from Git → the VM is **ready without intervention**. To combine with an SSH deploy key in cloud-init for private repos.

## 📚 Exercise 6 — Limits of pull mode

| Limitation | Impact |
|------------|--------|
| **No centralization** | Logs are on each node (`/var/log/ansible-pull.log`): aggregate via journalctl + rsyslog to a central Loki/ELK. |
| **No AAP Tower** | If you want the AAP UI, stay in push. AAP is strictly push. |
| **Node self-update** | Risk if a commit breaks `ansible-pull` itself → node stuck. Test in CI before merging to `main`. |
| **Drift undetectable from the center** | No aggregated "PLAY RECAP". An isolated node can drift without alerting. |

🔍 **Observation**: the **push pattern stays the default** for most fleets. **Pull** = niche **Edge / IoT / strict GitOps**. The EX294 does not test it because it targets **classic Red Hat datacenters**.

## 🔍 Observations to note

- **Push** = control node → targets (SSH). Default. AAP Tower compatible.
- **Pull** = target → Git repo. `ansible-pull -U <url>`. Not tested at EX294.
- **Cron / systemd timer** for periodic runs.
- **`cloud-init` + `ansible-pull`** = immutable bootstrap pattern.
- **No centralization** of logs: aggregate via syslog/Loki/ELK.
- Compatible with FQCN, collections, vault, all standard Ansible.

## 🤔 Reflection questions

1. Why is `ansible-pull` **better suited to IoT** than classic SSH push?
2. What security risk in running `ansible-pull` on an **unsigned** Git repo?
3. How do you **aggregate the logs** of 100 pull nodes into a central ELK?
4. Why does AAP / Automation Controller not support pull mode?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): create a mini local Git repo + run `ansible-pull` from db1.lab so that it drops a proof file.

## 💡 Going further

- **Lab 92 → 100 (RHCE mock)**: practice of the classic **push**.
- **`ansible-pull --vault-password-file`**: compatible with Vault.
- **systemd timer**: alternative to cron, better logging via journalctl.
- **GitOps Ansible**: combine `ansible-pull` + Argo Events / Flux to react to Git pushes.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/pratiques/ansible-pull-gitops/repo-pull/pull-playbook.yml
```

> 💡 **Tip**: `ansible-lint` validates the `pull-playbook.yml` exactly like a normal playbook (`hosts: localhost`, `connection: local`).
