# 🎯 Challenge — Argument specs with valid + invalid values

## ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** uses the `webserver`
role with **valid values** to demonstrate that:

1. The role runs without error on valid values.
2. The pytest test can **run the same solution with an invalid value
   passed via `--extra-vars`** and observe that `argument_specs` rejects it.

## 🧩 Stuck?

```bash
dsoxlab hint roles-argument-specs
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧩 Skeleton

```yaml
---
# Challenge: demonstrate that argument_specs automatically validates the inputs.
- name: Challenge - webserver avec argument_specs
  hosts: ???
  become: ???

  roles:
    - role: webserver
      vars:
        webserver_listen_port: ???       # The test expects 8090
        webserver_state: ???             # ← VALID choice among present/absent/latest
        webserver_service_state: ???     # ← VALID choice among started/stopped/restarted/reloaded
        webserver_index_content: "Lab 61 argument_specs validés sur {{ inventory_hostname }}"
```

> 💡 **Pitfalls**:
>
> - **Runtime validation**: `argument_specs.yml` generates an automatic
>   task `Validating arguments against arg spec 'main'` at the very
>   start of the role. If a value is invalid, the play **crashes before
>   executing a single task**.
> - **Strict `type: int`**: if you pass `webserver_listen_port: "8090"`
>   (quoted string), Ansible 2.18+ may accept and cast it, but
>   **some strict configurations** reject it. Prefer no
>   quotes for numbers.
> - **`choices:` case-insensitive**: no, it is case-sensitive. `Started`
>   ≠ `started`: strict respect of the value declared in `choices:`.
> - **Test with `--extra-vars`**: the conftest has no `_EXTRA_ARGS`
>   entry for this lab: the test's `--extra-vars` for
>   `valeur_invalide` are passed via the pytest test itself
>   (subprocess).

## 🚀 Run

### Normal run (valid values)

```bash
ansible-playbook labs/roles/argument-specs/challenge/solution.yml
```

🔍 The role runs normally, you see the
`Validating arguments against arg spec 'main'` task pass `ok`.

### Run with an INVALID value (by hand, to observe the message)

```bash
ansible-playbook labs/roles/argument-specs/challenge/solution.yml \
    --extra-vars "webserver_state=valeur_invalide"
```

🔍 Expected output:

```text
fatal: [db1.lab]: FAILED!
"argument_errors": [
  "value of webserver_state must be one of: present, absent, latest, got: valeur_invalide"
]
```

This is exactly what the pytest test reproduces to validate that argument_specs
is indeed active.

## 🧪 Automated validation

```bash
pytest -v labs/roles/argument-specs/challenge/tests/
```

The test checks:

- `nginx` installed on db1.
- `nginx.conf` contains `listen 8090` (proof of the
  `webserver_listen_port` override).
- The welcome page contains `argument_specs validés`.
- `meta/argument_specs.yml` exists and contains `argument_specs:` + `main:`.
- **The test re-runs the playbook with `webserver_state=valeur_invalide`** and
  checks that argument_specs rejects it: non-zero exit + message containing
  `must be one of`.

## 🧹 Reset

```bash
dsoxlab clean roles-argument-specs
```

## 💡 Going further

- **Document a `path:` option**: for file paths.
  `argument_specs` does not check existence: combine with `assert:`
  in the 1st task.
- **`type: dict` with nested `options:`**: validates the internal structure
  of a dict. Very powerful for complex configs.
- **Lint**:

  ```bash
  ansible-lint --profile production labs/roles/argument-specs/
  ```
