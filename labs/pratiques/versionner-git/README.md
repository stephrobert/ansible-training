# Versioning your playbooks with Git

> 💡 **Landing directly on this lab?** It is **self-contained** and **local**:
> everything happens on your control machine, no VM is needed. Only
> `git` must be installed (`git --version`).

## 🧠 Recap

🔗 [**Versioning your playbooks with Git**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/versionner-git/)

A playbook that is not versioned is a playbook you end up breaking without
being able to roll back. The official EX294 objective "Manage content in a
git repository" is **basic and concrete**: know how to initialize a repo, track
your files in it, commit, and push to a remote. Nothing more.

This lab fits into four everyday commands:

| Command | What it does |
| --- | --- |
| `git init` | creates an empty repo (the `.git/` folder) |
| `git add` | puts files under tracking (indexes them) |
| `git commit` | records a snapshot in the history |
| `git push` | sends the history to a remote |

No need for GitHub or GitLab to practice "push": a **local bare repo**
(`git init --bare`) plays exactly the role of a forge, on the same
host, without a network. This is what you are going to set up.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Initialize** a Git repo for a playbooks project (`git init -b main`).
2. **Set an author identity** on the repo (`git config user.name/email`).
3. **Track and commit** your playbooks (`git add`, `git commit -m`).
4. **Build a history** with several successive commits.
5. **Push** to a local bare remote (`git init --bare`, `git remote add`,
   `git push -u origin main`).

## 🔧 Preparation

No VM. Place yourself at the repo root:

```bash
cd $ANSIBLE_TRAINING
```

Check that Git is there:

```bash
git --version   # 2.x expected
```

## 📚 Exercise 1 — Initialize a repo

Create a project folder and initialize a repo in it on the `main` branch:

```bash
mkdir -p /tmp/mes-playbooks && cd /tmp/mes-playbooks
git init -b main
git status
```

🔍 **Observation**: `git status` announces "No commits yet" and lists your
files as *untracked*. The `.git/` folder has just appeared: this is the
repo.

## 📚 Exercise 2 — Set an identity

Git refuses to commit without knowing who you are. Set a **local**
identity for this repo:

```bash
git config user.name "Votre Nom"
git config user.email "vous@exemple.fr"
```

🔍 **Observation**: `--local` (the default here) writes to `.git/config`. This
identity is only valid for this repo, independent of your global config.

## 📚 Exercise 3 — Track and commit

Write a first playbook, index it, commit:

```bash
cat > site.yml <<'EOF'
---
- name: Point d entree
  hosts: all
  tasks:
    - name: Ping
      ansible.builtin.ping:
EOF

git add site.yml
git commit -m "Projet Ansible initial"
git log --oneline
```

🔍 **Observation**: `git add` moves `site.yml` from *untracked* to *staged*,
`git commit` records it. `git log` now shows one commit.

## 📚 Exercise 4 — Build a history

Add a second playbook and commit it separately:

```bash
cat > webserver.yml <<'EOF'
---
- name: Deployer le serveur web
  hosts: web
  tasks:
    - name: Installer httpd
      ansible.builtin.package:
        name: httpd
        state: present
EOF

git add webserver.yml
git commit -m "Ajout du playbook webserver"
git log --oneline
```

🔍 **Observation**: two commits, from the most recent to the oldest. This is
the history. Each commit is a complete snapshot, not a mere diff.

## 📚 Exercise 5 — Push to a local bare remote

No forge at hand? A **bare** repo takes its place:

```bash
git init --bare -b main /tmp/mes-playbooks.git
git remote add origin /tmp/mes-playbooks.git
git push -u origin main
git ls-remote /tmp/mes-playbooks.git
```

🔍 **Observation**: `git ls-remote` shows `refs/heads/main` pointing to the
**same SHA** as your local `git rev-parse HEAD`. The push did transfer
the history. A bare repo has no working tree: this is normal, it only
serves to receive commits.

## 🔍 Observations to note

- `git init` creates **nothing other** than the `.git/` folder: your files are
  only tracked after a `git add`.
- A file forgotten at commit stays visible in `git status`: a "clean"
  tree (empty `git status --porcelain`) is the proof that everything is recorded.
- A bare repo is the right target of a `push`: pushing it locally proves the
  gesture without depending on the network. In production, the `origin` would be a
  `https://` or `git@` URL, but the mechanics are identical.

## 🤔 Reflection questions

1. Why does Git refuse to commit as long as `user.email` is not set?
2. What is the difference between a bare repo and a normal repo, and why does a
   forge always serve bare repos?
3. You commit an Ansible `.retry` by mistake. How do you prevent it in
   the future, and why version a `.gitignore`?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to write a
`solution.sh` that **automates** the whole cycle: init, identity, add, two
commits, then push to a local bare. The tests inspect the **real state** of the
produced repo.

```bash
pytest -v labs/pratiques/versionner-git/challenge/tests/
```
