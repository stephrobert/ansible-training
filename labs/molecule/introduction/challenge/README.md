# 🎯 Challenge: write your first Molecule scenario

## ✅ Mission

The `webserver` role is shipped complete in `roles/`. The Molecule scenario,
however, is shipped as a **skeleton**: `molecule/default/{molecule.yml,
converge.yml, verify.yml}` contain `???` and empty lists.
Complete the three files to obtain a working scenario.

`create.yml`, `destroy.yml` and `prepare.yml` are **provided**: they are the
test harness, not the exercise. They still deserve a read, because they
explain the least intuitive point of Molecule v6+: the `default` driver
is **delegated**, it talks neither to Podman nor to Docker. These playbooks
are the ones that actually bring up the instance by calling `containers.podman`. Without
them, Molecule would skip the `create` step without flinching and the `converge`
would go knocking at the door of a machine that does not exist.

Expected state (this is what pytest checks):

| File | Expectation |
| --- | --- |
| `molecule.yml` | valid `driver`, at least 1 platform, `verifier` declared |
| `converge.yml` | applies the `webserver` role with `become: true` |
| `verify.yml` | at least 2 `ansible.builtin.assert` tasks that prove the state (nginx package, nginx.conf) |
| Everything | `molecule syntax` passes (pytest actually runs it) |

## 🧩 Hints

- The modern Molecule v6+ driver is called `default` (delegated): it is
  the Ansible collections (containers.podman...) that drive the
  instances.
- A platform is declared with `name`, `image`, `pre_build_image: true`,
  `command: /sbin/init` and `privileged: true` for a systemd container.
- In `verify.yml`, the pattern is: collect the state (`command` module
  with `changed_when: false`, or `stat`), then `ansible.builtin.assert`
  with `that:` and `fail_msg:`.
- Test as you go:

  ```bash
  cd labs/molecule/introduction
  ANSIBLE_ROLES_PATH=$PWD/roles molecule syntax
  molecule test        # full cycle if Podman is available
  ```

## 📓 Command log

When your scenario is ready, record in `challenge/solution.sh` the
Molecule commands you ran. This log must exist for
pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/molecule/introduction/challenge/tests/
```

The test loads your three YAML files, checks their semantics, then
actually runs `molecule syntax`.

## 🧹 Reset

```bash
dsoxlab clean molecule-introduction
```

## 💡 Going further

- Lab 63: enrich the config (prepare.yml, requirements.yml, test_sequence).
- Lab 64: full TDD cycle on a new role.
- Lab 65: multi-distro (RHEL + Debian + Ubuntu).
