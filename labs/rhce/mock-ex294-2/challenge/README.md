# Challenge — Mock RHCE EX294 #2: 19 tasks in 4 hours

## Exam conditions

- **Duration**: 4 hours on the clock.
- **Environment**: 4 VMs (`web1.lab`, `web2.lab`, `db1.lab`, `control-node.lab`).
- **Expected knowledge**: choice of the FQCN module, parameters, idempotence.
- **No external help**: offline Ansible doc (`ansible-doc`) allowed.
- **Success criterion**: the pytest tests green (19 tasks, several of them
  checked by more than one test).

## Prerequisites (to validate before starting the clock)

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping              # 4 'pong' attendus
```

The exam environment is **set** for you: as in the real Red Hat exam, the room
is ready and you do not have to build it.

- VG `vg_lab` present on `db1.lab` (T10).
- UID `3200` free on all the hosts (T7).
- Port 80 free on the `frontends` (nginx stopped) (T5/T6).
- `semanage` available on the `frontends` (verification of T8).

It is the lab's `setup.yaml` that sets this state, and it sets it **by undoing**
the expected result of the 19 tasks.

```bash
dsoxlab run rhce-mock-ex294-2     # plays the setup.yaml, then hands control back to you
```

Start the clock **after**.

## Imposed tree

All the files below are to be created **under the lab folder**:
`labs/rhce/mock-ex294-2/`.

```text
labs/rhce/mock-ex294-2/
├── inventory/
│   ├── hosts.yml
│   ├── group_vars/
│   │   ├── all.yml
│   │   └── frontends.yml
│   └── host_vars/
│       └── db1.lab.yml
├── .vault_password
├── vault.yml
├── roles/
│   └── web_publish/
└── challenge/
    └── solution.yml          ← the single playbook that orchestrates the 19 tasks
```

## Expected launch

```bash
ANSIBLE_ROLES_PATH=labs/rhce/mock-ex294-2/roles \
ansible-playbook \
    -i labs/rhce/mock-ex294-2/inventory/hosts.yml \
    --vault-password-file labs/rhce/mock-ex294-2/.vault_password \
    labs/rhce/mock-ex294-2/challenge/solution.yml
```

---

## The 19 tasks

### Task 1 — Static inventory

Produce `inventory/hosts.yml` in YAML format declaring:

- Group `frontends`: `web1.lab`, `web2.lab`.
- Group `backends`: `db1.lab`.
- Global variables for all the hosts:
  - `ansible_user: ansible` (the service account that dsoxlab provisions on the VMs).
  - `ansible_python_interpreter: /usr/bin/python3`
  - enough to reach the VMs without coding a single IP: the ssh_config generated
    by dsoxlab (`~/.cache/dsoxlab/ansible-training/ssh_config`) carries the real
    addresses and the key; pass it to OpenSSH via `ansible_ssh_common_args: -F <path>`.

`ansible-inventory -i inventory/hosts.yml --graph` must display the two groups
with their hosts.

### Task 2 — Hierarchical variables

Define:

| File | Variable | Value |
| --- | --- | --- |
| `inventory/group_vars/all.yml` | `deploy_stage` | `staging` |
| `inventory/group_vars/frontends.yml` | `pool_size` | `8` |
| `inventory/host_vars/db1.lab.yml` | `schema_name` | `lab200schema` |

On `web1.lab`, deposit the file `/tmp/lab200-vars.txt` (mode `0644`) that
contains at minimum the lines:

```text
deploy_stage: staging
pool_size: 8
```

### Task 3 — Vault

- Create `.vault_password` (mode `0600`) with a password of your choice.
- Create `vault.yml`, **encrypted**, containing the variable:
  - `api_token: "Ex294-Deux!"`
- Load this file in the playbook via `vars_files:`.
- On `db1.lab`, write `/tmp/lab200-token.txt` (mode `0600`) containing the
  decrypted value of `api_token`.

### Task 4 — Template

On `db1.lab`, deposit `/tmp/lab200-service.conf`:

- mode `0600`, owner `svcuser`, group `svcgroup` (see task 7).
- content generated from a Jinja2 template including **at minimum** the Ansible
  hostname and the value of `schema_name` (the string `lab200schema` must appear).

### Task 5 — Packages

Install on **all** the hosts: `httpd`, `valkey`, `python3-libselinux`.

### Task 6 — Services

- On `frontends`: `httpd` enabled at boot and started.
- On `db1.lab`: `valkey` enabled at boot and started.

### Task 7 — Users and groups

On **all** the hosts:

- Group `svcgroup` (GID `3200`).
- User `svcuser` (UID `3200`, primary group `svcgroup`, shell `/bin/bash`).
- The user `svcuser` must be able to run `/usr/bin/journalctl` via `sudo`
  **without entering a password** (only this command).

### Task 8 — SELinux

On `frontends`, enable the SELinux boolean `httpd_can_network_connect_db`
**permanently** (survives the reboot).

> 💡 On this exam the web server is Apache (`httpd`), which runs in the SELinux
> domain `httpd_t`. The boolean `httpd_can_network_connect_db` lets a page served
> by Apache open a network connection to a database. Check it with
> `ps -eZ | grep httpd`.

### Task 9 — Firewalld

- On `frontends`: open the services `http` and `https`.
- On `db1.lab`: open the **port `6379/tcp`** (the valkey port).

The rules must be **persistent** (reboot) **and active immediately** (no need for
`firewall-cmd --reload` after the playbook).

### Task 10 — LVM storage

On `db1.lab`, in the existing VG `vg_lab`:

- Create an LV `lv_app` of **400 MB**.
- Format it in **ext4**.
- Mount it on `/srv/appdata`, with an `fstab` entry that **persists at reboot**.

### Task 11 — Role `web_publish`

Create a role `web_publish` (under `roles/web_publish/`) that, on the `frontends`:

- Deposits `/var/www/html/index.html` from a Jinja2 template containing at least
  the inventory hostname.
- Guarantees that `httpd` is active (idempotent, task 6 has already done it, your
  role must not break).
- Defines a handler `Restart httpd` notified if the template changes.

The `solution.yml` invokes this role for the `frontends`.

### Task 12 — Loops and conditions

On `db1.lab`, create 6 files `/tmp/slot1` to `/tmp/slot6`:

- **even** number (2, 4, 6): content `even`.
- **odd** number (1, 3, 5): content `odd`.

The 6 files must be created in **a single task** with a loop.

### Task 13 — Incident handling

On `db1.lab`, the playbook must attempt to start the service `lab200-agent`. No
package of the distribution provides this service: the attempt **really fails**,
on every pass. This is intended.

- The task that fails is named **exactly** `Lancer l'agent lab200`.
- The failure must **not** interrupt the playbook. For `db1.lab`, the
  `PLAY RECAP` must display `failed=0`.
- The incident must be **caught**, not passed over in silence: the `PLAY RECAP`
  must display `rescued=1` and `ignored=0`. Silencing the error is rejected.
- **Only in case of failure**: write `/tmp/lab200-incident.txt` (mode `0644`)
  containing, on a line of its own, the name of the task that failed **as Ansible
  reports it**. This name is read at runtime, it is not copied out.
- **In all cases**, success as well as failure: write
  `/tmp/lab200-incident-fin.txt` (mode `0644`).

### Task 14 — Rolling deployment

On the `frontends`, the deployment must be done **in waves of a single host at a
time**, in inventory order (`web1.lab`, then `web2.lab`).

- Each host deposits `/tmp/lab200-palier-<inventory_hostname>.txt` (mode `0644`,
  owner `root`). Example: `/tmp/lab200-palier-web1.lab.txt`.
- The content of the marker must be **stable from one pass to the next**.
- Between two waves, the deployment must observe a **stabilization time of at
  least 6 seconds**.

> The verification is based on the **timestamps** (`mtime`) of the two markers:
> that of `web1.lab` must precede that of `web2.lab` by at least 3 seconds.

### Task 15 — Centralized deployment log

From a play that targets the **`frontends`**, write the log
`/tmp/lab200-central-log.txt` (mode `0644`, owner `root`) **on `db1.lab`**.

- It must contain **exactly one line**, whatever the number of frontends, and
  replaying the playbook must not add any.
- This line must name the **frontend** at the origin of the write (its
  `inventory_hostname`) and carry the value of `pool_size` (see task 2).
- The file must exist **on no** frontend.

### Task 16 — Scheduled task

On `db1.lab`, schedule a report in the **crontab of the user `svcuser`** (see
task 7), that is the one that `crontab -l -u svcuser` returns:

- schedule: every day at **22h30**;
- command: `/usr/bin/date >> /tmp/lab200-audit.log 2>&1`;
- one entry and only one: replaying the playbook must not duplicate it.

### Task 17 — Task selection by tags

On `db1.lab`, four tasks, each depositing its marker in mode `0644`:

| Task | Marker | Must run |
| --- | --- | --- |
| Init marker | `/tmp/lab200-tag-init.txt` | under the tag `init` |
| Publish marker | `/tmp/lab200-tag-publish.txt` | under the tag `publish` |
| Systematic marker | `/tmp/lab200-tag-always.txt` | **always**, including under `--tags publish` |
| Destructive purge | `/tmp/lab200-tag-purge.txt` | **never**, except under `--tags purge` requested explicitly |

The purge, in addition to depositing its marker, removes those of init and
publish.

The two behaviors verified, on real runs:

- **Without `--tags`**: init, publish and systematic are deposited; the purge did
  **not** happen.
- **With `--tags publish`**: publish and systematic are deposited; init and purge
  are **absent**.

### Task 18 — Custom fact

On the `frontends`, publish a custom fact that any fact collection will find:

- directory `/etc/ansible/facts.d` (mode `0755`, owner `root`);
- file `lab200.fact` (mode `0644`, owner `root`), in **INI** format, section
  `[audit]`, with two keys:
  - `stage`: the value of `deploy_stage` (see task 2);
  - `pool`: the value of `pool_size` (see task 2).

The values must **come from the inventory**, not be copied in hard.

The verification does not open the file: it asks Ansible what it retrieves from
it. The following command must return `ansible_local.lab200.audit.stage` and
`ansible_local.lab200.audit.pool` on **both** frontends:

```bash
ansible frontends -i inventory/hosts.yml \
    -m ansible.builtin.setup -a filter=ansible_local
```

### Task 19 — Content Collection via `requirements.yml`

The EX294 objective **"Install Content Collections and use them in playbooks"**
is not proven by any of the previous tasks: add it.

Write a **`requirements.yml`** declaring **one** collection from Ansible Galaxy,
its version **pinned in strict semver** (`ansible.posix` version `1.6.2`).
Install it into a **project-local directory** (not the home), with the install
step made **idempotent** (`creates:` on `ansible-galaxy`).

Then, from `db1.lab`:

- Deposit `/tmp/lab200-collections.txt` (mode `0644`, owner `root`) containing the
  output of `ansible-galaxy collection list` for that install path. It must name
  the collection **and** its pinned version.
- **Use** a module **from the installed collection**: `ansible.posix.sysctl`
  writes the kernel parameter `vm.swappiness` to the value `25`, applied and
  persisted in the file `/etc/sysctl.d/99-lab200-collection.conf`.

> The verification does not read your `requirements.yml`: it checks the state it
> produced. A `requirements.yml` that declares the right sources but is never
> installed leaves no `1.6.2` in the collection list, and a `vm.swappiness` still
> at its default proves no module of the collection ran.

---

## Validation

```bash
pytest -v labs/rhce/mock-ex294-2/challenge/tests/
```

The success scale is in the root README of the lab. Several tasks have two or
three tests, because an RHCE task is rarely failed as a whole. You can open a
port without making it permanent, enable a SELinux boolean that drops back at
reboot, mount a volume without an fstab entry, or grant `svcuser` a sudo much
broader than requested: each time the state is right at time T and wrong after
reboot, or right and dangerous. These are exactly the points that the real exam
sanctions.

## Reset

```bash
dsoxlab clean rhce-mock-ex294-2
```

## 💡 Going further

- **`ansible-lint --profile production`**: validate the quality of your solution.
- **Idempotence**: rerun the solution a second time. A `PLAY RECAP` with
  `changed=0` everywhere confirms a clean playbook. A test checks it.
