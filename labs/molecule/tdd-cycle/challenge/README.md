# Tests written after the code always agree with the code

## The situation

The team's roles are all tested, and the tests never catch anything. The reason
is visible in the git history: the tasks are written first, the assertions are
written afterwards, and they end up describing what the code happens to do
rather than what was asked for. You are starting a new `users` role, and this
time the order is reversed: nothing gets written until a test demands it.

Your mission, from the project directory:

1. Write the **assertions first**, on a role whose tasks do not exist yet, and
   run the cycle to watch them fail. A test that has never failed proves nothing.
2. Declare the role's input contract before its code: the shape and type of the
   list of users to create, so a bad call is rejected up front.
3. Only then write the **minimum** tasks that turn the assertions green, looping
   over the requested users rather than hardcoding any of them.
4. Refactor the role once green, and use the suite as your safety net: it must
   stay green through the rewrite, or it was never protecting you.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-tdd-cycle/ (in French)

## 🎯 Challenge: a real TDD cycle with Molecule

### ✅ Mission

The `users` role is shipped with its **contract** (`meta/argument_specs.yml`,
`defaults/main.yml`) and its **input data** (`converge.yml` creates
alice with /bin/zsh and wheel, bob, carol). Two files are empty, and
that is the whole point of the lab: you write them **in TDD order**.

1. **RED**: write `molecule/default/verify.yml`, the tests first.
   At least 4 `ansible.builtin.assert` assertions that specify the
   expected behavior (see the skeleton comments). Run
   `molecule converge && molecule verify`: verify must be **red**
   (the role is empty, this is normal and it is the starting point).
2. **GREEN**: write `roles/users/tasks/main.yml`, the minimum that makes
   your tests pass: a loop over `users_to_create` with the
   `ansible.builtin.user` module. Re-run `molecule verify`: **green**.
3. **REFACTOR**: clean up (loop_control, labels...) while keeping the green.

Expected state (this is what pytest checks):

| Item | Expectation |
| --- | --- |
| `verify.yml` | at least 4 `ansible.builtin.assert` tasks with `that:` and `fail_msg:`, covering alice (shell + group), bob and carol |
| `tasks/main.yml` | loop (`loop:`) over `users_to_create`, `ansible.builtin.user` module, `users_default_shell` fallback, `append: true` for the groups |
| `converge.yml` | unchanged: it is the contract data |
| Everything | `molecule syntax` passes (pytest actually runs it) |

### 🧩 Stuck?

```bash
dsoxlab hint molecule-tdd-cycle
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

Record in `challenge/solution.sh` the sequence you actually ran
(converge, verify red, implementation, verify green). This log must
exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/tdd-cycle/challenge/tests/
```

The full execution proof (`molecule test`, requires Podman) is marked `slow`
and now runs **by default** with the command above (about 24 seconds, image
cached). In a constrained environment (no Podman), deselect it with `-m 'not
slow'`:

```bash
pytest -v -m 'not slow' labs/molecule/tdd-cycle/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean molecule-tdd-cycle
```

### 💡 Going further

- Add a `dave` user in converge.yml: which tests do you write
  first?
- `molecule idempotence`: the second run of the role must be changed=0.
- Compare with the testinfra verifier from lab 66.
