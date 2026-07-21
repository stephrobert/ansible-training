# Lab — `replace:` module (replace a pattern in a file)

> 💡 **Self-contained lab.** Prerequisite: `ansible all -m ansible.builtin.ping` returns `pong`.

## 🧠 Recap

🔗 [**Ansible replace module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-replace/)

`ansible.builtin.replace:` substitutes **all occurrences** of a regex pattern in
a file, without touching the rest of the line or the file. It is the tool for
**cross-cutting changes**: updating an API URL, changing a hostname, propagating
a new version.

**Key difference with `lineinfile:`**: `replace:` modifies a **partial pattern**
anywhere in the file; `lineinfile:` modifies a **whole line**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Substitute** a pattern everywhere in a file.
2. **Limit** the zone with `before:` and `after:`.
3. **Preserve** part of the pattern via capture groups.
4. **Distinguish** `replace:` from `lineinfile:` depending on the need.
5. **Diagnose** idempotence broken by a double run.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m copy -a "dest=/etc/myapp.conf content='url=http://api-old.example.com/v1\nport=8080\n[server]\nssl_enabled=false\n[client]\nssl_enabled=false\n'"
```

## 📚 Exercise 1 — Simple substitution of all occurrences

```yaml
---
- name: Demo replace
  hosts: db1.lab
  become: true
  tasks:
    - name: Forcer https sur les URL d'API
      ansible.builtin.replace:
        path: /etc/myapp.conf
        regexp: 'http://api-old\.example\.com'
        replace: 'https://api.example.com'
```

Run it twice and check idempotence (2nd run = `ok`).

## 📚 Exercise 2 — Limit with before/after

```yaml
- name: Activer SSL UNIQUEMENT dans la section [server]
  ansible.builtin.replace:
    path: /etc/myapp.conf
    after: '\[server\]'
    before: '\[client\]'
    regexp: 'ssl_enabled\s*=\s*false'
    replace: 'ssl_enabled = true'
```

**Verify**: `ssl_enabled` stays `false` in the `[client]` section.

> ⚠️ **Pitfall validated in lab**: with `before:` and `after:`, the `^` anchor
> does **not** propagate Python's MULTILINE mode. If you write
> `regexp: '^ssl_enabled...'` with before/after, the regexp matches **only the
> very beginning** of the extracted zone (not each line) and the substitution
> fails silently. **Solution**: remove the `^` when combining with
> before/after, the restricted zone context is enough to avoid false matches
> in other sections.

## 📚 Exercise 3 — Idempotence pitfalls

Deliberately break idempotence to understand:

```yaml
- ansible.builtin.replace:
    path: /etc/myapp.conf
    regexp: 'http'         # trop large
    replace: 'https://http' # contient toujours 'http' → idempotence cassée
```

Run it twice → the 2nd run = `changed` as well. Understand why.

## 🔍 Observations to note

- **Idempotence**: a second run of the playbook must show `changed=0` on all
  the tasks of the `ansible.builtin.replace` module. If a task stays
  `changed=1`, the regex/condition is not anchored correctly (see exercises).
- **Explicit FQCN**: `ansible.builtin.replace` (and not its short name),
  `ansible-lint --profile production` checks it.
- **`validate:`** when it is available (lineinfile, copy, template): an external
  binary checks the syntax of the file before writing, which avoids breaking a
  service with an invalid config.
- **Targeting convention**: this lab targets **db1.lab** (a single host to
  isolate the destructive impact).

## 🤔 Reflection questions

1. When should you use `ansible.builtin.replace` rather than `lineinfile:`
   (single unique line) or `blockinfile:` (delimited block)? List 2 cases where
   each alternative would be preferable (readability, idempotence, performance).

2. If you had to substitute a pattern everywhere in a file on **50 servers in
   parallel**, which Ansible parameters (`forks`, `serial`, `strategy`) would
   you adjust to hold a 5-minute SLA?

3. How do you handle the case where the module fails **partially** (success on
   some tasks, failure on others)? Which strategies allow resuming without
   replaying everything (`block/rescue`, `--start-at-task`, state marker)?

## 🚀 Final challenge

Once the exercises above are digested, run the **standalone challenge**:

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-fichiers/replace --challenge
# ou
cat labs/modules-fichiers/replace/challenge/README.md
```

The challenge asks you to write your `challenge/solution.yml` without looking at
the exercises. Validation via `pytest`:

```bash
pytest -v labs/modules-fichiers/replace/challenge/tests/
```

## 💡 Going further

- Combine `ansible.builtin.replace` with **`backup: true`** to keep a
  timestamped copy of the original file before modification, useful for
  rollback.
- Study **`check_mode: true`** + `--diff`: Ansible shows you what it would do
  without applying anything. Indispensable in production.
- Compare the **performance** between 1 `ansible.builtin.replace` task × 10 and
  1 `template:` task that generates the whole file at once, the template is
  often faster AND more readable when the number of changes grows.

## 🧹 Cleanup

```bash
`dsoxlab clean <id-du-lab>`
```

## 📂 Solution

See `solution/modules-fichiers/replace/solution.yml`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-fichiers/replace/lab.yml
ansible-lint labs/modules-fichiers/replace/challenge/solution.yml
ansible-lint --profile production labs/modules-fichiers/replace/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows RHCE 2026 best practices.
