# Mock RHCE EX294 #2 (4h clock, 19 tasks)

> 💡 **Landing directly on this lab?** Every lab in this repo is
> **self-contained**. Single prerequisite: the 4 lab VMs must respond to the
> Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Preparing for the RHCE (EX294)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/)

The **RHCE EX294** exam is **performance-based**: 4 hours, live RHEL/AlmaLinux
environment, writing complete playbooks over 15 to 20 tasks. This lab is a
**second mock**, a variant of `rhce/mock-ex294`: the **same 19 categories**, but
**every concrete value differs**. If you already did mock #1, none of your
answers can be copied here: the stack is **Apache + valkey** instead of
nginx + mariadb, the users, LVM layout, ports, SELinux boolean, cron schedule,
tags, custom fact and installed collection are all different. Same skills,
different situation. **Time yourself.**

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Manage an exam against the clock**: prioritize, do not get stuck, come back.
2. **Cover** the 19 standard EX294 categories on an unfamiliar target.
3. **Check** each task **immediately** after writing it.
4. **Identify** your **persistent weaknesses** by category to revise in a
   targeted way.

## 📋 The 19 tasks of mock #2

| # | Category | Task | Target host |
|---|-----------|-------|------------|
| 1 | **Inventory** | Static inventory with 2 groups (`frontends`, `backends`) and `ansible_python_interpreter` | local |
| 2 | **Variables** | Define `group_vars` and `host_vars` (`deploy_stage`, `pool_size`, `schema_name`) | all |
| 3 | **Vault** | Encrypt a `vault.yml` (`api_token`), consume it in a playbook | all |
| 4 | **File modules** | Deposit a templated file (`template`) mode `0600`, owner `svcuser` | `db1.lab` |
| 5 | **Package modules** | Install `httpd`, `valkey`, `python3-libselinux` via `dnf` | all |
| 6 | **Services** | Enable + start `httpd` and `valkey` via `systemd` | `frontends` + `db1.lab` |
| 7 | **Users** | Create `svcuser` (UID 3200) + group `svcgroup` (GID 3200) with sudo NOPASSWD limited to `journalctl` | all |
| 8 | **SELinux** | Enable `httpd_can_network_connect_db` (permanent boolean) | `frontends` |
| 9 | **Firewalld** | Open `http`/`https` on frontends, port `6379/tcp` on db1 (`permanent`+`immediate`) | `frontends` + `db1.lab` |
| 10 | **Storage** | Create an LV `lv_app` of 400M, ext4 fs, mounted on `/srv/appdata` (fstab) | `db1.lab` |
| 11 | **Role** | Write a role `web_publish` that combines 2 modules + 1 handler + 1 template | `frontends` |
| 12 | **Conditions/Loops** | Loop that creates 6 files `/tmp/slot{1..6}` with content depending on parity | `db1.lab` |
| 13 | **Error handling** | Catch the real failure of a task (`rescued=1`, `ignored=0`), record its trace, continue | `db1.lab` |
| 14 | **Rolling deployment** | Process the frontends one at a time, with stabilization between waves | `frontends` |
| 15 | **Delegation** | Write a single log on `db1.lab` from a play that targets the frontends | `frontends` → `db1.lab` |
| 16 | **Scheduled tasks** | Daily report at 22h30 in `svcuser`'s crontab | `db1.lab` |
| 17 | **Tags** | Tasks selectable by `--tags`, a systematic tag and a purge kept out of reach | `db1.lab` |
| 18 | **Custom facts** | Publish `lab200` in `/etc/ansible/facts.d`, and prove that it comes back up | `frontends` |
| 19 | **Content Collections** | Install a pinned collection from a `requirements.yml`, prove it is resolvable, then use one of its modules | `db1.lab` |

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping

# Sets the "exam room" state on the 4 VMs, then hands back control
dsoxlab run rhce-mock-ex294-2
```

The lab's `setup.yaml` **undoes** the expected result of the 19 tasks before
handing control back to you: SELinux boolean to `off`, firewalld services and
port closed, `httpd` and `valkey` uninstalled, `svcuser` removed, `/srv/appdata`
unmounted, `svcuser`'s crontab and `lab200` fact removed, markers erased, nginx
stopped so port 80 is free. A previous run gives you no points. It sets what the
statement declares provided by the environment: the VG `vg_lab` on `db1.lab`,
the UID 3200 free, port 80 free.

## ⚙️ Target tree

```text
labs/rhce/mock-ex294-2/
├── README.md                       ← this page
├── setup.yaml                      ← the "exam room" state
├── cleanup.yaml                    ← the reset afterwards
├── inventory/                      ← tasks 1 and 2
└── challenge/
    ├── README.md                   ← the statement with the 19 detailed tasks
    └── tests/
        └── test_functional.py      ← pytest tests for the 19 tasks
```

The learner writes themselves:

- `inventory/hosts.yml` and its `group_vars`/`host_vars` (tasks 1 and 2)
- encrypted `vault.yml` + `.vault_password` (task 3)
- `roles/web_publish/...` (task 11)
- **A single** `challenge/solution.yml` that orchestrates **the 19 tasks** in
  order.

> The `inventory/` you write is the deliverable of tasks 1 and 2: it is not
> delivered with the statement, and it is gitignored. The instructor's reference
> solution has its own, encrypted under `solution/`, which you cannot read.

## 📚 Exam strategy

### Before starting (5 minutes)

1. **Read the 19 statements** of the `challenge/README.md` in full.
2. **Identify** the 2-3 tasks that seem the hardest → plan more time.
3. **Check** that `ansible all -m ping` answers `pong` everywhere.

### During the exam (≤ 4h clock)

- **One task at a time**. Write the task + run the playbook + check manually.
- **Stuck > 10 minutes**? **Skip** and come back later.
- **`ansible-doc <module>`** for a quick reminder of a parameter.

### Final validation (15 minutes)

```bash
pytest -v labs/rhce/mock-ex294-2/challenge/tests/
```

The 19 tasks are covered by the pytest suite: the trickiest ones have several
tests, because an RHCE task is rarely failed as a whole. A port open but not
permanent, a SELinux boolean that drops back at reboot, a volume mounted without
an fstab entry, a `NOPASSWD` much broader than requested: each time the state is
right at time T and wrong after reboot, or right and dangerous. This is what the
real exam sanctions, so it is tested separately.

The tests never check that a command was typed, nor what your YAML says: they
look at the machine. For tasks 13 to 19, this means the counters of the
`PLAY RECAP`, the timestamps of the markers, the number of lines of a log,
`crontab -l -u svcuser`, a real `--tags` run, a collection of facts and the
resolved `ansible-galaxy collection list`. A good file obtained by the wrong
means does not pass.

Your score:

| Score | Verdict |
| --- | --- |
| full green | ✅ Ready for the real exam |
| 1-2 red | ⚠️ Revise the failed categories before attempting the exam |
| 3-6 red | 🔁 Redo the mock in 1 week after targeted revision |
| more | ❌ Go back over the corresponding course sections |

## 🤔 Classic pitfalls in the real EX294

- **Quote `mode: "0644"`** otherwise YAML interprets it as octal then decimal → mode `420`.
- **`firewalld`** without `immediate: true` → permanent rule not active until reload.
- **`SELinux`**: forgetting `python3-libselinux` on the target → `template`/`copy` fail.
- **`ansible-vault`**: forgetting `--vault-password-file` at launch.
- **`hosts: all`** instead of `hosts: frontends` → the task runs everywhere.
- **`become: true`** forgotten on privileged tasks (firewalld, dnf, systemd).

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0` everywhere.
- **Explicit FQCN**: prefer `ansible.builtin.<module>` (or the appropriate
  collection) over the short name.
- **Targeting convention**: `hosts: all` here means the 3 managed nodes
  (`web1.lab`, `web2.lab`, `db1.lab`), not the 4 VMs of the fleet.
- **Isolated reset**: `dsoxlab clean rhce-mock-ex294-2` undoes what the solution
  set up so you can replay the scenario from scratch.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): the **19 detailed tasks**, in
the order of the expected playbook.

## 💡 Going further

- Did you also finish `rhce/mock-ex294`? Two full mocks with different values are
  the best way to prove you learned the **skill**, not the answer.
- **`ansible-lint --profile production`** on your playbook: zero warning expected.
