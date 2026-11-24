# "Show me what it will change, before it changes it"

## The situation

The change advisory board asks the same question before every run on
**db1.lab**, and it is a fair one: *what exactly is this playbook going to
touch?* Last quarter a playbook rewrote a file under `/etc` nobody expected it
to touch, and "it should be fine" did not survive the post-mortem. New rule:
every change is rehearsed dry, its diff is read out loud, and only then does
the same playbook run for real.

You drill that workflow from **control-node.lab** on a harmless marker file.

Your mission:

1. Write a play that drops `/etc/lab-checkmode.txt` on `db1.lab`, mode `0644`,
   with a known content.
2. Run it **`--check --diff`** first: read the before/after block, then confirm
   on `db1.lab` that nothing was actually written.
3. Run it for real and check the diff matches exactly what the dry run
   announced.
4. Run it a third time: no diff, `changed=0`. Then learn which modules cannot
   simulate, and how to force a read-only task to run even in check mode.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/checkmode-diff/ (in French)

## 🎯 Challenge — `--check --diff` then real execution

### ✅ Objective

Write `challenge/solution.yml` that lays down a file `/etc/lab-checkmode.txt` on
**db1.lab** containing the string **`Lab checkmode validé`**.

The pedagogical goal: demonstrate the **audit → execution** workflow:

1. **Audit**: you first run in `--check --diff` to visualize what *will*
   change, without writing anything.
2. **Real execution**: once the diff is validated, you rerun without `--check`.

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-checkmode-diff
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch in two steps

#### 1. Audit in `--check --diff`

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/challenge/solution.yml \
    --check --diff
```

🔍 **What you should see**:

- `PLAY RECAP`: `changed=1` (intent)
- A diff block showing `before:` (empty) → `after:` (your content)
- **On the db1 side**, the file does **not exist yet**:

   ```bash
   ansible db1.lab -b -m ansible.builtin.command -a "ls /etc/lab-checkmode.txt"
   # Doit retourner: ls: cannot access ...: No such file or directory
   ```

#### 2. Real execution

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/challenge/solution.yml --diff
```

🔍 **What you should see**:

- `PLAY RECAP`: `changed=1` (this time for real)
- The diff identical to the audit one
- The file is laid down on db1:

   ```bash
   ansible db1.lab -m ansible.builtin.command -a "cat /etc/lab-checkmode.txt"
   ```

#### 3. Check idempotence

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/challenge/solution.yml --diff
```

🔍 `changed=0`, **no diff** shown. This is the steady state.

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/checkmode-diff/challenge/tests/
```

The test checks on db1:

- `/etc/lab-checkmode.txt` exists.
- Its content includes `Lab checkmode validé`.

> ⚠️ The root `conftest.py` automatically plays your `solution.yml` before
> the tests (fixture `_apply_lab_state`). If pytest **skips** with a message
> *"Aucun challenge/solution.yml ni solution.sh trouvé"*, it means you must
> first write `solution.yml`!

### 🧹 Reset (replay the scenario from scratch)

```bash
dsoxlab clean ecrire-code-checkmode-diff
```

This target removes `/etc/lab-checkmode.txt` on the db1 side to replay the audit
diff "from blank" (the diff must show an addition again).

### 🚀 Going further

- **Reproduce the audit**: run `dsoxlab clean <id-du-lab>` then re-run `--check --diff`
  to clearly see the "creation from nothing" diff. Compare with a `--check
  --diff` when the file is already laid down (idempotence: no diff).
- **`check_mode: false`**: add a `command:` task that reads the version of a
  binary (`openssl version`) with `check_mode: false` and `changed_when: false`.
  Check that it runs even in `--check` (proof: the output is
  capturable via `register:` and usable in a `debug:`).
- **Lint with `ansible-lint`**: before running your playbook, validate its
  quality with:

   ```bash
   ansible-lint labs/ecrire-code/checkmode-diff/challenge/solution.yml
   ```

   If `ansible-lint` returns without error, the YAML follows best
   practices (FQCN, `name:` on every task, modes as strings, etc.). You
   can also run the `production` profile (the strictest):

   ```bash
   ansible-lint --profile production \
       labs/ecrire-code/checkmode-diff/challenge/solution.yml
   ```
