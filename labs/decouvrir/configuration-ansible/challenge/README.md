# 🎯 Challenge — Project `ansible.cfg` with `profile_tasks` enabled

## ✅ Objective

Create a lab-level `ansible.cfg` that enables **`profile_tasks`** + forces **`forks=20`** + uses **`stdout_callback = yaml`**, then run a playbook that drops **the output of `ansible-config dump --only-changed`** into a file on `db1.lab`.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab03a-config.txt` |
| Permissions | `0644`, owner `root` |
| Content | Output of `ansible-config dump --only-changed` (≥3 non-empty lines) |
| `ansible.cfg` must contain | `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks` |

## 🧩 Hints

### Step 1 — `ansible.cfg`

Create `labs/decouvrir/configuration-ansible/ansible.cfg` with at least:

```ini
[defaults]
forks = ???
stdout_callback = ???
callbacks_enabled = ???
host_key_checking = False
```

### Step 2 — `solution.yml` skeleton

```yaml
---
- name: Challenge 03a — config Ansible
  hosts: ???
  become: ???
  gather_facts: false

  tasks:
    - name: Capturer la config active
      ansible.builtin.command: ansible-config dump --only-changed
      register: ???
      changed_when: ???                # ← read-only
      delegate_to: localhost
      become: false

    - name: Déposer la sortie sur db1.lab
      ansible.builtin.copy:
        dest: ???
        content: "{{ ???.stdout }}\n"
        owner: ???
        group: ???
        mode: ???
```

> 💡 **Pitfalls**:
> - **`delegate_to: localhost`** + **`become: false`** on the first task because `ansible-config` runs on the **control node** (the learner's machine), not on the target.
> - **`changed_when: false`** on the read command to preserve idempotence.
> - **`cd` is NOT enough, and that is the lab's trap.** Your playbook lives in
>   `challenge/`, yet a `delegate_to: localhost` task runs with the PLAYBOOK's
>   folder as the current directory. From `challenge/`, Ansible therefore never
>   sees the `ansible.cfg` you just wrote at the lab root.
>   Measured: `ansible-config dump` does not mention it, and the test fails.
>   You must explicitly designate the file, for example with an
>   `environment: ANSIBLE_CONFIG: ...` at the play level. This is exactly
>   exercise 1: `ANSIBLE_CONFIG` is the HIGHEST precedence source.

## 🚀 Launch

```bash
cd labs/decouvrir/configuration-ansible/
ansible-playbook challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/decouvrir/configuration-ansible/challenge/tests/
```

The pytest test validates:

- `/tmp/lab03a-config.txt` exists on `db1.lab` with mode `0644`, owner `root`.
- ≥3 non-empty lines in the content.
- The lab's `ansible.cfg` does contain `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks`.

## 🧹 Reset

```bash
dsoxlab clean decouvrir-configuration-ansible
```

## 💡 Going further

- **`ansible-config init --disabled > ansible.cfg`**: generates an exhaustive documented config file.
- **Env variables**: `ANSIBLE_FORKS=50` overrides without touching the file.
- **`ansible-lint`** does not check the content of `ansible.cfg`. To validate the syntax: `ansible-config view`.
