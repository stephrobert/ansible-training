# An identifier nobody should have to type

## The situation

The support tool correlates incidents by a system identifier: short hostname,
then running kernel. Today someone builds that string by hand and pastes it
into the ticket, and gets it wrong roughly one time in five — usually right
after a kernel update, when the machine no longer runs what the ticket claims.
The host knows both halves perfectly well. You only have to ask it, assemble
the answer, and write it down.

You do it on **db1.lab** from **control-node.lab**, without gathering the full
fact set.

Your mission:

1. Capture the **short hostname** and the **running kernel** with two read-only
   commands, keeping each result.
2. Make sure those reads never report `changed`: a command that only looks at
   the system changes nothing, and must say so, or your playbook is never
   idempotent again.
3. Assemble the two captured values into a single **runtime fact**.
4. Write it on db1 as `system_id=<hostname>:<kernel>`, and know where a
   `set_fact` sits in the precedence order — and what `cacheable` changes.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/register-set-fact/ (in French)

## 🎯 Challenge — `register` then `set_fact` to compute an identifier

### ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Retrieves 2 pieces of system information via `ansible.builtin.command` + `register`.
2. Combines these 2 pieces of information into a **runtime fact** via `set_fact`.
3. Places the result into `/tmp/system-id.txt` (format `system_id=<hostname>:<kernel>`).

### 🧩 The register → set_fact pattern

This is a very common pattern in production: you **read** several values with
`command:`, you **assemble** them with `set_fact:`, then you **use** them in
the following tasks (template, copy, debug…).

#### Skeleton

```yaml
---
- name: Challenge - register puis set_fact
  hosts: db1.lab
  become: true
  gather_facts: false   # we prove we can do everything without gather

  tasks:
    - name: Récupérer le hostname court
      ansible.builtin.command: ???      # shell command that returns the short hostname
      register: ???
      changed_when: false               # read-only cmd, so never changed

    - name: Récupérer la version du noyau
      ansible.builtin.command: ???      # shell command that returns the kernel version
      register: ???
      changed_when: false

    - name: Construire system_id
      ansible.builtin.set_fact:
        system_id: "{{ ???.stdout }}:{{ ???.stdout }}"

    - name: Poser /tmp/system-id.txt
      ansible.builtin.copy:
        dest: /tmp/system-id.txt
        content: "system_id={{ system_id }}\n"
        mode: "0644"
```

#### Command hints

- Short hostname: the `hostname -s` command (Linux) returns `db1` (without the
  `.lab` domain).
- Kernel version: the `uname -r` command returns something like
  `5.14.0-503.40.1.el9_1.x86_64`.

#### Ansible hints

- **`register: var_name`** captures a task's result into a variable.
  The result contains `stdout`, `rc`, `start`, `end`, etc.
- **`changed_when: false`**: indispensable on read-only `command:`,
  otherwise Ansible marks the task as `changed` on every run (`command:` is
  not idempotent by default).
- **`set_fact:`** creates a variable at level **19** in the precedence
  (above the play's `vars:` and `vars_files:`, below `--extra-vars`).

### 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/register-set-fact/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/system-id.txt"
# Must display: system_id=db1:5.14.0-...el9_x.x86_64
```

> 💡 **Traps**:
>
> - **`register:`** captures `stdout`, `rc`, `failed`, `changed`, etc.
>   For the useful content: `<var>.stdout` (raw string), `.stdout_lines`
>   (list).
> - **`set_fact:`** creates a variable persistent at the play level (not
>   at all cases). Useful to turn a `register:` into a clean
>   variable.
> - **`changed_when: false`** on read-only `command:` / `shell:`:
>   otherwise they are marked `changed=1` on every run, breaking
>   idempotence. For a `hostname`, `uname`, etc.
> - **`set_fact` is level 19**, higher than the play's `vars:` (12) and
>   than `vars_files:` (14), but below `--extra-vars` (22). So an
>   `--extra-vars` can override a `set_fact`.

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/register-set-fact/challenge/tests/
```

The test verifies on db1:

- `/tmp/system-id.txt` exists.
- Contains `system_id=db1:` (proof the hostname was captured).
- Contains `.el9` or `.x86_64` (proof the kernel was captured).

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-register-set-fact
```

### 💡 Going further

- **Using `ansible_facts`** instead of `command:`: `ansible_facts.hostname`
  and `ansible_facts.kernel` are already collected by `gather_facts`. Compare
  the two approaches in terms of simplicity.
- **Multi-host**: on a play targeting several hosts, `set_fact` is
  **per-host**. Demonstrate it by targeting `webservers` and placing a file
  per host (`/tmp/system-id-{{ inventory_hostname }}.txt`).
- **`cacheable: yes`** on `set_fact`: the value is cached (useful if
  fact_caching is enabled).
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/register-set-fact/challenge/solution.yml
   ```
