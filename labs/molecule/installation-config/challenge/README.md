# The test suite that passes on a lie

## The situation

Your Molecule scenario is green, and it proves almost nothing. The instance
starts bare, so the role installs its own prerequisites and the test never
exercises the real starting state. The run pulls no collections, so it passes
locally and explodes in CI. Nobody knows which task eats the four minutes. And
the cycle never re-runs the role, so a role that changes something on every pass
still reports success. A green suite that cannot fail is decoration.

Your mission, from the project directory:

1. Pre-condition the instance before the role runs, so the test starts from the
   state a real host would be in, and declare the Galaxy dependencies the
   scenario needs instead of relying on what happens to be installed.
2. Give each instance its own variables, so the scenario stops assuming every
   platform is identical.
3. Pin the cycle's step order explicitly, and make sure the **idempotence** step
   is part of it: the suite must be able to catch a role that never settles.
4. Turn on task timing, and name the slowest step.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-installation-config/ (in French)

## 🎯 Challenge: enrich the Molecule configuration

### ✅ Mission

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
| `molecule.yml`: callbacks | `callbacks_enabled` with `profile_tasks` and `timer` |
| Everything | `molecule syntax` passes (pytest actually runs it) |

Warning: `verify.yml` (provided) checks that nginx listens on the
overridden port. If your `host_vars` is absent or wrong, a full `molecule test`
will fail.

### 🧩 Stuck?

```bash
dsoxlab hint molecule-installation-config
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

When your configuration is ready, record in `challenge/solution.sh`
the Molecule commands you ran. This log must exist for pytest
to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/installation-config/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean molecule-installation-config
```

### 💡 Going further

- `MOLECULE_PLAYBOOK`: environment variable to substitute the
  converge playbook (pattern `${MOLECULE_PLAYBOOK:-converge.yml}`).
- `molecule test --destroy=never`: keep the instance for inspection.
