# Lab — `lineinfile:` module (modify a line in a file)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```

## 🧠 Recap

🔗 [**Ansible lineinfile module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-lineinfile/)

`ansible.builtin.lineinfile:` modifies **a single line** in an existing file:
add if absent, replace a line identified by a regexp, or remove. It is the basic
tool to **edit a configuration file** where you control just a few parameters:
`sshd_config`, `sudoers`, `/etc/hosts`, `/etc/sysctl.conf`.

**Key difference with `blockinfile:`**: `lineinfile:` = 1 line, `blockinfile:` = multi-line block with automatic markers.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Add** a line if absent, do nothing if present (idempotent).
2. **Replace** a line identified by a regexp.
3. **Remove** a line with `state: absent`.
4. **Validate** the syntax before writing (`validate: "sshd -t -f %s"`).
5. **Preserve** part of the line via `backrefs: true`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak"
```

## 📚 Exercise 1 — Add an idempotent line

Create `lab.yml`:

```yaml
---
- name: Demo lineinfile — ajout simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Activer le forwarding IPv4
      ansible.builtin.lineinfile:
        path: /etc/sysctl.conf
        line: "net.ipv4.ip_forward=1"
        state: present
```

Run it twice and observe:

```bash
ansible-playbook labs/modules-fichiers/lineinfile/lab.yml
ansible-playbook labs/modules-fichiers/lineinfile/lab.yml   # → 2e run = ok (idempotent)
```

## 📚 Exercise 2 — Replace via regexp + validate

```yaml
- name: Désactiver le login root SSH
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^\s*#?\s*PermitRootLogin\s'
    line: "PermitRootLogin no"
    state: present
    validate: "sshd -t -f %s"
  notify: Restart sshd
```

**To test**: modify the regexp so that it no longer matches, verify that the
line is added at the end of the file instead of being replaced.

## 📚 Exercise 3 — Backrefs

```yaml
- name: Réduire MaxAuthTries SSH en gardant le format
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^(\s*MaxAuthTries\s+).*$'
    line: '\g<1>3'
    backrefs: true
    validate: "sshd -t -f %s"
```

**Observe**: with `backrefs: true`, if the regexp does not match, the line is
**NOT added** (crucial difference).

## 🔍 Observations to note

- **Idempotence**: a second run of the playbook must show `changed=0` on all
  the tasks of the `ansible.builtin.lineinfile` module. If a task stays
  `changed=1`, the regex/condition is not anchored correctly (see exercises).
- **Explicit FQCN**: `ansible.builtin.lineinfile` (and not its short name),
  `ansible-lint --profile production` checks it.
- **`validate:`** when it is available (lineinfile, copy, template): an external
  binary checks the syntax of the file before writing, which avoids breaking a
  service with an invalid config.
- **Targeting convention**: this lab targets **db1.lab** (a single host to
  isolate the destructive impact).

## 🤔 Reflection questions

1. When should you use `ansible.builtin.lineinfile` rather than `replace:`
   (multi-occurrence regex) or `template:` (whole file generated)? List 2 cases
   where each alternative would be preferable (readability, idempotence,
   performance).

2. If you had to modify config files line by line on **50 servers in parallel**,
   which Ansible parameters (`forks`, `serial`, `strategy`) would you adjust to
   hold a 5-minute SLA?

3. How do you handle the case where the module fails **partially** (success on
   some tasks, failure on others)? Which strategies allow resuming without
   replaying everything (`block/rescue`, `--start-at-task`, state marker)?

## 🚀 Final challenge

Once the exercises above are digested, run the **standalone challenge**:

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-fichiers/lineinfile --challenge
# ou
cat labs/modules-fichiers/lineinfile/challenge/README.md
```

The challenge asks you to write your `challenge/solution.yml` without looking at
the exercises. Validation via `pytest`:

```bash
pytest -v labs/modules-fichiers/lineinfile/challenge/tests/
```

## 💡 Going further

- Combine `ansible.builtin.lineinfile` with **`backup: true`** to keep a
  timestamped copy of the original file before modification, useful for
  rollback.
- Study **`check_mode: true`** + `--diff`: Ansible shows you what it would do
  without applying anything. Indispensable in production.
- Compare the **performance** between 1 `ansible.builtin.lineinfile` task × 10
  and 1 `template:` task that generates the whole file at once, the template is
  often faster AND more readable when the number of changes grows.

## 🧹 Cleanup

```bash
`dsoxlab clean <id-du-lab>`
```

Or manually:

```bash
ansible db1.lab -b -m shell -a "cp /etc/ssh/sshd_config.bak /etc/ssh/sshd_config && systemctl restart sshd"
```

## 📂 Solution

See `solution/modules-fichiers/lineinfile/solution.yml`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-fichiers/lineinfile/lab.yml
ansible-lint labs/modules-fichiers/lineinfile/challenge/solution.yml
ansible-lint --profile production labs/modules-fichiers/lineinfile/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows RHCE 2026 best practices.
