# Lab 73 — `ansible-galaxy` CLI: full tour

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Ansible installed. No VMs needed (purely local lab).

## 🧠 Recap

🔗 [**ansible-galaxy CLI**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-galaxy-cli/)

`ansible-galaxy` is the CLI tool to **manage roles and collections**:
create, install, list, verify, build, publish. There are **2 parallel
subcommands**: `role` and `collection`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Initialize a new role with `ansible-galaxy role init`.
2. Initialize a collection with `ansible-galaxy collection init`.
3. Install a role/collection from Galaxy or Git.
4. List what is installed locally.
5. Build a collection (`.tar.gz`).
6. Publish to Galaxy with an API token.
7. Verify integrity (`verify`).

## 🔧 Preparation

```bash
ansible-galaxy --version
```

## ⚙️ Directory tree

```text
labs/galaxy/ansible-galaxy-cli/
├── README.md
├── cheatsheet.md          ← quick command reference (to study)
└── roles/webserver/        ← example role
```

## 📚 Exercise 1 — Read `cheatsheet.md`

The shipped file covers all the essential subcommands:

| Command | Effect |
| --- | --- |
| `ansible-galaxy role init <nom>` | Creates the skeleton of a new role |
| `ansible-galaxy collection init <ns.col>` | Creates the skeleton of a collection |
| `ansible-galaxy role install <user.role>` | Installs a role from Galaxy |
| `ansible-galaxy collection install <user.col>` | Installs a collection from Galaxy |
| `ansible-galaxy role install -r requirements.yml` | Installs from a requirements file |
| `ansible-galaxy collection install -r requirements.yml` | Same for collections |
| `ansible-galaxy role list` | Lists the installed roles |
| `ansible-galaxy collection list` | Lists the installed collections |
| `ansible-galaxy collection build` | Creates a `.tar.gz` from a collection |
| `ansible-galaxy collection publish *.tar.gz --token=TOK` | Publishes to Galaxy |
| `ansible-galaxy collection verify <user.col>` | Verifies integrity (signature) |

## 📚 Exercise 2 — Initialize a role

```bash
cd /tmp
ansible-galaxy role init mon_role
ls mon_role/
# defaults/  files/  handlers/  meta/  README.md  tasks/  templates/  tests/  vars/
```

🔍 **Observation**: 8 folders + README + tests/. This is the **standard
skeleton** of a Galaxy role.

## 📚 Exercise 3 — Initialize a collection

```bash
ansible-galaxy collection init monorg.macollection
ls monorg/macollection/
# docs/  galaxy.yml  meta/  plugins/  README.md  roles/
```

🔍 **Observation**: `galaxy.yml` is the collection **manifest**
(equivalent of a role's `meta/main.yml`, but for a collection).

## 📚 Exercise 4 — Install a role

```bash
ansible-galaxy role install geerlingguy.docker
# → ~/.ansible/roles/geerlingguy.docker/

ansible-galaxy role list
# → lists all installed roles with their version
```

## 📚 Exercise 5 — Install a collection

```bash
ansible-galaxy collection install community.docker
# → ~/.ansible/collections/ansible_collections/community/docker/

ansible-galaxy collection list
# → lists all installed collections
```

## 📚 Exercise 6 — Build + Publish a collection

```bash
cd monorg/macollection
ansible-galaxy collection build
# → monorg-macollection-1.0.0.tar.gz

ansible-galaxy collection publish monorg-macollection-1.0.0.tar.gz \
    --token=$GALAXY_API_TOKEN
```

🔍 **Observation**: to publish, you need a **Galaxy token** (account on
[galaxy.ansible.com](https://galaxy.ansible.com/) → Preferences → API Key).

## 🔍 Observations to note

- **Role vs Collection**: a role is simpler (a single role), a
  collection can group roles + plugins + modules + docs.
- **Galaxy 2026** favors **collections** over standalone roles. A
  standalone role can be wrapped in a collection for the
  publication.
- **`requirements.yml`** is the equivalent of Node's `package.json` or
  Python's `requirements.txt`. Covered in lab 74.
- **`collection verify`**: verifies integrity (hash). Important if
  you distribute via a private repo.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to a
   fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to tune to keep execution times acceptable?

2. Which alternative Ansible modules could you have used to reach
   the same result? What are their trade-offs (guaranteed idempotence,
   performance, external collection dependency)?

3. If a playbook step fails mid-run, what is the impact
   on the hosts already processed? How do you make the scenario resumable
   (`block/rescue/always`, `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`--ignore-errors`**: continues despite an error on one of the items
  (useful in CI).
- **`--force`**: reinstalls even if already present.
- **`--namespace`**: namespace prefix (you can have several).
- **Token in `~/.ansible.cfg`** instead of `--token=`:
  `[galaxy] server_list = primary; [galaxy_server.primary]
  url=https://galaxy.ansible.com/ token=...`.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/galaxy/ansible-galaxy-cli/
```
