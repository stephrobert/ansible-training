# 🎯 Challenge: enrich the Molecule configuration

## ✅ Mission

The `molecule/default/` scenario is shipped in its **minimal** version from
lab 62 (converge.yml, verify.yml, create.yml and destroy.yml are provided).
Your job: the configuration enrichments, which you write
yourself.

`prepare.yml`, however, is the only harness playbook you must write:
it is precisely the subject of this lab. Without it, the instance stays bare and the
`converge` fails.

Expected state (this is what pytest checks):

| Item | Expectation |
| --- | --- |
| `molecule/default/requirements.yml` | To create: collections needed by the scenario (ansible.posix, containers.podman...) with a version constraint |
| `molecule.yml`: `dependency` | `dependency.options.requirements-file` wired to your `requirements.yml` |
| `molecule/default/prepare.yml` | To create: instance preparation play (prerequisites outside the role's scope) |
| `molecule.yml`: `host_vars` | `provisioner.inventory.host_vars` overrides `webserver_listen_port: 8080` for the instance |
| `molecule.yml`: `test_sequence` | custom sequence under `scenario:`, including `prepare`, `converge`, `idempotence` and `verify` |
| `molecule.yml`: callbacks | `callback_enabled` with `profile_tasks` and `timer` |
| Everything | `molecule syntax` passes (pytest actually runs it) |

Warning: `verify.yml` (provided) checks that nginx listens on the
overridden port. If your `host_vars` is absent or wrong, a full `molecule test`
will fail.

## 🧩 Hints

- `dependency.name: galaxy` accepts `options.requirements-file` to
  point to a scenario dependencies file.
- `prepare.yml` is played once after `create`, before `converge`:
  perfect to install `procps-ng` and `iproute` (diagnostics) that are
  not the role's responsibility.
- Two prerequisites, not one. `verify.yml` needs `ss` (package
  `iproute`) to observe the listening port, but the **role itself** needs
  `firewalld`: it opens its port with `ansible.posix.firewalld`.
  On a VM the daemon already runs; in a container, it does not, and the
  `converge` dies on "firewalld is not running". Installing the package is not
  enough, you also have to start the service. A role that **configures**
  a firewall has no business **installing** one: it is up to the test harness to
  provide the machine in the expected state.
- Contrary to a widespread belief, Molecule's default sequence
  already plays `prepare`. Declaring your `test_sequence` therefore does not serve
  to enable it, but to remove the steps you do not have (`cleanup`,
  `side_effect`) and to make the contract explicit.
- The default sequence is overridden like this:

  ```yaml
  scenario:
    name: default
    test_sequence:
      - ...
  ```

- Test as you go:

  ```bash
  cd labs/molecule/installation-config
  ANSIBLE_ROLES_PATH=$PWD/roles molecule syntax
  ```

## 📓 Command log

When your configuration is ready, record in `challenge/solution.sh`
the Molecule commands you ran. This log must exist for pytest
to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/molecule/installation-config/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean molecule-installation-config
```

## 💡 Going further

- `MOLECULE_PLAYBOOK`: environment variable to substitute the
  converge playbook (pattern `${MOLECULE_PLAYBOOK:-converge.yml}`).
- `molecule test --destroy=never`: keep the instance for inspection.
