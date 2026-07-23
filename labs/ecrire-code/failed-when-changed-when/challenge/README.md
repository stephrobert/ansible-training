# 🎯 Challenge — Map a return code to Ansible semantics

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**, turns a command returning
**rc=1** (so a *failure* by Ansible default) into a success, but marked as
`changed`.

Why? Some commands use rc=1 as a **business signal** (`grep` finding nothing,
`diff` detecting differences, etc.). Without `failed_when`, the play would stop
wrongly.

## 🧩 Expected semantics

| Return code | Desired Ansible semantics |
| --- | --- |
| `rc=0` | `ok` (nothing to do) |
| `rc=1` | `changed` (business change detected, not a failure) |
| `rc=2,3,…` | `failed` (real error) |

## 🧩 Keywords to combine

- **`register: result`**: capture the result (in particular `result.rc`).
- **`failed_when:`**: redefines what is considered a failure.
- **`changed_when:`**: redefines what is considered a change.

```yaml
- name: ...
  ansible.builtin.command: ???
  register: result
  failed_when: result.rc not in [???]    # list of rc considered OK
  changed_when: result.rc == ???          # which rc triggers "changed"
```

## 🧩 Skeleton

```yaml
---
- name: Challenge - failed_when et changed_when
  hosts: db1.lab
  become: true

  tasks:
    - name: Commande qui retourne rc=1
      ansible.builtin.command: /bin/sh -c 'exit 1'
      register: result
      failed_when: ???
      changed_when: ???

    - name: Marqueur (atteint = preuve que la 1ère tâche n'a pas planté)
      ansible.builtin.copy:
        dest: /tmp/failed-when-result.txt
        content: "rc={{ result.rc }} ok=changed\n"
        mode: "0644"
```

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/failed-when-changed-when/challenge/solution.yml
```

🔍 **Expected output**:

- 1st task: `changed` (not `failed`).
- 2nd task: `changed` (the file is written).
- `PLAY RECAP`: `changed=2, failed=0`.

> 💡 **Pitfalls**:
>
> - **`failed_when:`** redefines the failure condition. By default, a
>   task fails if `rc != 0`. With `failed_when: result.rc not in [0, 2]`,
>   codes 0 and 2 are OK.
> - **`changed_when:`** redefines the `changed` condition. Without it, a
>   `command:` or `shell:` is **always** marked `changed=1` (anti-
>   idempotence). For a read-only one: `changed_when: false`.
> - **`changed_when:` + `failed_when:` together**: `failed_when` is
>   evaluated first; if the task fails, `changed_when` is not
>   evaluated.
> - **Boolean expression**: `failed_when: result.stdout != ""` (non-empty
>   string), `failed_when: "'ERROR' in result.stderr"` (substring).

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/failed-when-changed-when/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-failed-when-changed-when
```

## 💡 Going further

- **`failed_when: result.stderr`**: you fail if stderr is non-empty
  (useful for commands that return rc=0 but write a blocking warning
  to stderr).
- **`changed_when: '"already exists" not in result.stdout'`**: you are
  changed only if the output does not indicate the thing already exists
  (equivalent to a `creates:` but via stdout parsing).
- **Difference with `block/rescue`**: `failed_when`/`changed_when`
  reinterpret **one** task. `block/rescue` orchestrates **several**
  tasks around a failure.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/failed-when-changed-when/challenge/solution.yml
   ```
