# 🎯 Challenge — Combine INI custom facts + Bash script

## ✅ Objective

Drop **two** custom facts on `db1.lab` (one static INI + one dynamic Bash script), then in a playbook **read both** and write a proof file that combines the values.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Custom fact 1 | `/etc/ansible/facts.d/lab14a.fact` (INI, mode `0644`) |
| Custom fact 2 | `/etc/ansible/facts.d/lab14a-uptime.fact` (Bash script, mode `0755`) |
| Produced file | `/tmp/lab14a-custom-facts.txt` |
| Permissions | `0644`, owner `root` |
| Content | Values of the 2 facts (at least 4 lines) |

## 🧩 Hints

### `solution.yml` skeleton

```yaml
---
- name: Challenge 14a — custom facts INI + script Bash
  hosts: ???
  become: ???
  gather_facts: false           # ← we will collect explicitly after dropping the facts

  tasks:
    - name: Créer /etc/ansible/facts.d/
      ansible.builtin.file:
        path: ???
        state: ???
        mode: ???

    - name: Déposer le custom fact INI
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/lab14a.fact
        mode: ???                # ← STATIC, non-executable
        content: |
          [project]
          name = lab14a
          version = ???
          [team]
          owner = ???

    - name: Déposer le custom fact dynamique
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/lab14a-uptime.fact
        mode: ???                # ← EXECUTABLE
        content: |
          #!/bin/bash
          cat <<EOF
          {
            "uptime_seconds": $(awk '{print int($1)}' /proc/uptime),
            "kernel": "$(uname -r)"
          }
          EOF

    - name: Re-collecter les facts pour récupérer ansible_local
      ansible.builtin.setup:
        filter: ???                # ← isolate the custom facts

    - name: Déposer le fichier preuve
      ansible.builtin.copy:
        dest: /tmp/lab14a-custom-facts.txt
        content: |
          project: {{ ansible_local.lab14a.project.name }}
          version: {{ ansible_local.lab14a.project.version }}
          owner: {{ ???.???.team.owner }}
          kernel: {{ ???.???.kernel }}
        mode: ???
```

> 💡 **Traps**:
> - The **executable bit** (`mode: "0755"`) of the dynamic script is **critical**: without it, Ansible reads it as static and crashes because it is not valid JSON/INI.
> - The **2nd fact** is named `lab14a-uptime.fact` → accessible via `ansible_local.lab14a-uptime` (the `-` stays in the key).
> - **Re-collect the facts** after dropping them: `ansible.builtin.setup` is necessary because `gather_facts: false` initially.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/custom-facts/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/custom-facts/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-custom-facts
```

## 💡 Going further

- **Custom path**: `setup -a "fact_path=/custom/path"` to avoid using the default `/etc/ansible/facts.d/`.
- **`ansible-lint --profile production`** must return green.
