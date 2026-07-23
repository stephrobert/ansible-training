# Lab 92 — Mock RHCE EX294 (4h clock, 19 tasks)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Preparing for the RHCE (EX294)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/certifications/rhce/)

The **RHCE EX294** exam is **performance-based**: 4 hours, live RHEL/AlmaLinux environment, writing complete playbooks over 15 to 20 tasks covering **inventories**, **variables**, **conditions**, **loops**, **roles**, **file/service/user/SELinux/firewalld management**, **ansible-vault**, **error handling**, **rolling deployment**, **delegation**, **tags**, **scheduled tasks** and **custom facts**. No multiple choice. Success = **every executed playbook returns `failed=0`**.

This lab simulates a full exam: **19 independent tasks**, 4 hours, validation by pytest. **Time yourself**. If you finish in 3h00, you are ready for the real exam.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Manage an exam against the clock**: prioritize, do not get stuck, come back.
2. **Cover** the 19 standard EX294 categories (see below).
3. **Check** each task **immediately** after writing it (not everything at the end of the exam).
4. **Identify** your **persistent weaknesses** by category to revise in a targeted way.

## 📋 The 19 tasks of the mock

| # | Category | Task | Target host |
|---|-----------|-------|------------|
| 1 | **Inventory** | Create a static inventory with 2 groups (`webservers`, `dbservers`) and `ansible_python_interpreter` | local |
| 2 | **Variables** | Define `group_vars` and `host_vars`, check precedence | all |
| 3 | **Vault** | Encrypt a `vault.yml` file with `ansible-vault encrypt`, consume it in a playbook | all |
| 4 | **File modules** | Deposit a templated file (`copy` + `template`) with mode `0640`, owner `app` | `db1.lab` |
| 5 | **Package modules** | Install `nginx`, `mariadb-server`, `python3-libselinux` via `dnf` | all |
| 6 | **Services** | Enable + start `nginx` and `mariadb` via `systemd` | `webservers` + `db1.lab` |
| 7 | **Users** | Create user `appuser` (UID 2001) + group `appgroup` (GID 2001) with sudo NOPASSWD limited to `systemctl` | all |
| 8 | **SELinux** | Enable `httpd_can_network_connect` (permanent boolean) | `webservers` |
| 9 | **Firewalld** | Open `http`/`https`/`mysql` (`permanent: true, immediate: true`) | `webservers` + `db1.lab` |
| 10 | **Storage** | Create an LV `lv_data` of 300M, xfs fs, mounted on `/mnt/data` (fstab) | `db1.lab` |
| 11 | **Role** | Write a role `app_deploy` that combines 2 modules + 1 handler + 1 template | `webservers` |
| 12 | **Conditions/Loops** | Loop that creates 5 files `/tmp/file{1..5}` with content depending on parity | `db1.lab` |
| 13 | **Error handling** | Catch the real failure of a task (`rescued=1`, `ignored=0`), record its trace, continue | `db1.lab` |
| 14 | **Rolling deployment** | Process the webservers one at a time, with stabilization between waves | `webservers` |
| 15 | **Delegation** | Write a single log on `db1.lab` from a play that targets the webservers | `webservers` → `db1.lab` |
| 16 | **Scheduled tasks** | Daily report at 04h05 in `appuser`'s crontab | `db1.lab` |
| 17 | **Tags** | Tasks selectable by `--tags`, a systematic tag and a purge kept out of reach | `db1.lab` |
| 18 | **Custom facts** | Publish `lab100` in `/etc/ansible/facts.d`, and prove that it comes back up | `webservers` |
| 19 | **Content Collections** | Install a pinned collection from a `requirements.yml`, prove it is resolvable, then use one of its modules | `db1.lab` |

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping

# Sets the "exam room" state on the 4 VMs, then hands back control
dsoxlab run rhce-mock-ex294
```

The lab's `setup.yaml` **undoes** the expected result of the 19 tasks before
handing control back to you: SELinux boolean to `off`, firewalld services closed,
`nginx` and `mariadb-server` uninstalled, `appuser` removed, `/mnt/data`
unmounted, `appuser`'s crontab and `lab100` fact removed, markers erased. A previous run, yours or that of another lab, gives you
no points. On the other hand it sets what the statement declares provided by the
environment: the VG `vg_lab` on `db1.lab`, the UID 2001 free, port 80
free.

## ⚙️ Target tree

```text
labs/rhce/mock-ex294/
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
- `roles/app_deploy/...` (task 11)
- **A single** `challenge/solution.yml` that orchestrates **the 19 tasks** in
  order.

> The `inventory/` you write is the deliverable of tasks 1 and 2: it is not
> delivered with the statement, and it is gitignored. The instructor's reference
> solution has its own, encrypted under `solution/`, which you cannot read.

## 📚 Exam strategy

### Before starting (5 minutes)

1. **Read the 19 statements** of the `challenge/README.md` in full.
2. **Identify** the 2-3 tasks that seem the hardest -> plan more time.
3. **Check** that `ansible all -m ping` answers `pong` everywhere.

### During the exam (≤ 4h clock)

- **One task at a time**. Write the task + run the playbook + check manually.
- **Stuck > 10 minutes**? **Skip** and come back later.
- **`ansible-doc <module>`** for a quick reminder of a parameter.
- **`ansible-doc -l | grep <word>`** to find an FQCN module.

### Final validation (15 minutes)

```bash
pytest -v labs/rhce/mock-ex294/challenge/tests/
```

The 19 tasks are covered by the pytest suite: the trickiest ones have
several, because an RHCE task is rarely failed as a whole. A port open
but not permanent, a SELinux boolean that drops back at reboot, a volume mounted
without an fstab entry, a `NOPASSWD` much broader than requested: each time
the state is right at time T and wrong after reboot, or right and dangerous.
This is what the real exam sanctions, so it is tested separately.

The tests never check that a command was typed, nor what
your YAML says: they look at the machine. For tasks 13 to 19, this means
the counters of the `PLAY RECAP`, the timestamps of the markers, the number
of lines of a log, `crontab -l -u appuser`, a real `--tags` run, a
collection of facts and the resolved `ansible-galaxy collection list`. A good
file obtained by the wrong means does not pass.

Your score:

| Score | Verdict |
| --- | --- |
| 30/30 | ✅ Ready for the real exam |
| 26-29/30 | ⚠️ Revise the failed categories before attempting the exam |
| 20-25/30 | 🔁 Redo the mock in 1 week after targeted revision |
| < 20/30 | ❌ Go back over the corresponding course sections |

## 📚 Exercise 1 — Start the clock

```bash
date '+Démarrage : %Y-%m-%d %H:%M:%S' | tee /tmp/lab100-start.txt
```

Stop when you launch the final `pytest`. Compare to 4h.

## 🤔 Classic pitfalls in the real EX294

- **Quote `mode: "0644"`** otherwise YAML interprets it as octal then decimal -> mode `420` (read-only).
- **`name:` ending with `:`** -> breaks YAML 1.2. Always quote.
- **`firewalld`** without `immediate: true` -> permanent rule not active until reload.
- **`SELinux`**: forgetting `python3-libselinux` on the target -> `template`/`copy` fail.
- **`ansible-vault`**: forgetting `--vault-password-file` at launch.
- **`hosts: all`** instead of `hosts: webservers` -> the task runs everywhere, breaks the inventory.
- **`become: true`** forgotten on privileged tasks (firewalld, dnf, systemd).

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  compliant with best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name. `ansible-lint --profile
  production` checks it.
- **Targeting convention**: `hosts: all` here means the 3 managed nodes
  (`web1.lab`, `web2.lab`, `db1.lab`), and not the 4 VMs of the fleet: the control
  node is not in the lab inventory, the exam does not manage it. It is your
  `inventory/hosts.yml` from task 1 that decides, not the fleet.
- **Isolated reset**: `dsoxlab clean rhce-mock-ex294` undoes what the solution set
  up (LV, mount, fstab entry, `appuser`, sudo rule, boolean, ports) so you can
  replay the scenario from scratch.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to a
   fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to adjust to keep acceptable execution times?

2. Which alternative Ansible modules could you have used to reach
   the same result? What are their trade-offs (guaranteed idempotence,
   performance, external collection dependency)?

3. If a playbook step fails during execution, what is the impact
   on the hosts already processed? How do you make the scenario resumable
   (`block/rescue/always`, `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): the **18 detailed tasks**, in the order of the expected playbook.

## 💡 Going further

- **Mock 2**: redo this lab in 1 week, aim for a shorter time.
- **`ansible-navigator`**: a real EX294 objective (use Automation content navigator to find modules in collections and build inventories). Also testing your playbook in `community-ansible-dev-tools` (lab 84) guarantees portability.
- **`ansible-lint --profile production`** on your playbook: zero warning expected.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/rhce/mock-ex294/challenge/solution.yml
ansible-lint --profile production labs/rhce/mock-ex294/challenge/solution.yml
```

> 💡 **At the real exam**, `ansible-lint` is **not** an official criterion,
> but a playbook that passes the `production` profile also passes the exam
> in 99% of cases (explicit FQCN, quoted modes, idempotence respected).
