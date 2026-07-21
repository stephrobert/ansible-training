# 🎯 Challenge — The webserver role declares its prerequisites, db1 proves it

## ✅ Objective

The `webserver` role shipped in `roles/` has two structural prerequisites that its
callers constantly forget: SELinux in the right mode, and a firewall
started with the right ports. Your work happens in two places:

1. **`roles/webserver/meta/main.yml`**: declare the `dependencies:` so
   that `selinux_setup` then `firewall_setup` run **before** the role,
   with their variables.
2. **`challenge/solution.yml`**: a play that consumes **only** the
   `webserver` role (via `roles:`) on db1.lab, with `webserver_listen_port: 8081`.
   Nobody calls the dependencies: the role imposes them.

The tests do not read `meta/main.yml`: they check **the state of db1.lab**.
Each role in the lab records its passage in `/tmp/deps-order.txt`: this
file is the proof of the real execution order.

## 🧩 Expected contract (state of db1.lab)

| Proof | Expected state |
| --- | --- |
| Execution order | `/tmp/deps-order.txt` contains exactly `selinux_setup`, `firewall_setup`, `webserver`, in this order |
| Dependency 1 executed | `getenforce` returns `Enforcing` (var `selinux_setup_state: enforcing` passed by the dependency) |
| Dependency 2 executed | `firewalld` started **and** enabled, port **443/tcp** open (var `firewall_setup_open_ports` passed by the dependency) |
| Parent role executed | nginx installed, started, enabled, listening on **8081**, port 8081/tcp open, welcome page in place |

## 🧩 Skeletons

`roles/webserver/meta/main.yml` (part to complete):

```yaml
dependencies:
  - role: ???
    vars:
      selinux_setup_state: ???
  - role: ???
    vars:
      firewall_setup_open_ports:
        - ???
```

`challenge/solution.yml`:

```yaml
---
- name: Déployer webserver (les prérequis suivent tout seuls)
  hosts: ???
  become: ???
  gather_facts: false
  roles:
    - role: ???
      vars:
        webserver_listen_port: ???
```

> 💡 **Pitfalls**:
>
> - **`ANSIBLE_ROLES_PATH=labs/roles/dependencies/roles`** at launch:
>   the roles are not next to `solution.yml` (pytest does it for you).
> - **The dependency order is the declaration order**: declare
>   `selinux_setup` before `firewall_setup`, otherwise `/tmp/deps-order.txt`
>   will tell another story and the test will see it.
> - **The play must NOT list the dependencies** in `roles:`: if you
>   call them by hand, you have recreated the scenario's problem (each
>   caller has to remember). The whole point of `dependencies:` is that the role
>   imposes them itself.
> - **`443/tcp`** in firewalld format, with the quotes.

## 🚀 Run

```bash
ANSIBLE_ROLES_PATH=labs/roles/dependencies/roles \
  ansible-playbook labs/roles/dependencies/challenge/solution.yml
```

🔍 In the output, the tasks prefixed `selinux_setup :` and
`firewall_setup :` appear **before** those of the `webserver` role, even though
the play mentions them nowhere.

## 🧪 Validation

```bash
pytest -v labs/roles/dependencies/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean roles-dependencies
```

## 💡 Going further

- **The diamond**: add a `common` role that both `selinux_setup`
  AND `firewall_setup` depend on. Re-run: `common` appears only once in
  `/tmp/deps-order.txt` (deduplication), unless both reference it
  with different `vars:`.
- **`allow_duplicates: true`** in the dependency role's `meta/main.yml`:
  it then runs on every reference.
- **`ansible-lint --profile production labs/roles/dependencies/challenge/solution.yml`**:
  expected output `Passed: 0 failure(s), 0 warning(s)`.
