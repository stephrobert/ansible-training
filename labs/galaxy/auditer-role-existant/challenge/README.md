# A stranger's code, running as root, on your production

## The situation

A developer wants a Galaxy role added to the project by Friday. It has plenty of
stars, so the discussion is treated as settled. It is not. That role is arbitrary
code that will run with **`become: true`** on every production server you own,
and nobody in the room has opened it. Stars measure popularity, not whether the
thing downloads a binary over plain HTTP or has been abandoned since 2021.

Your mission, from the project directory:

1. Turn the vague feeling of "it looks fine" into a **scored checklist**, over
   six axes: maintainer health, code quality, security, tests, compatibility and
   idempotence.
2. Read the role's own declared identity to find which platforms it actually
   claims to support, and confront that with the fleet you run.
3. Hunt the classic tells: hardcoded secrets, unencrypted downloads, short module
   names, arbitrary commands with nothing to make them idempotent.
4. Turn the score into a **decision** you can defend: adopt, fork, or refuse.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/auditer-role-existant/ (in French)

## 🎯 Challenge: audit a real third-party role, verified conclusions

### ✅ Mission

The lab ships in `vendor/thirdparty_backup/` a third-party role like the
ones found on Galaxy or GitHub: short, practical... and riddled with
problems. Audit it with the methodology from `AUDIT_CHECKLIST.md` (at the
lab root) and record your **factual** conclusions in
`challenge/audit.yml`.

Pytest recomputes each fact directly from the role's code and
compares it to your report: an audit copy-pasted without reading the role will
not pass.

Exact expected format for `challenge/audit.yml`:

```yaml
---
role: thirdparty_backup
has_argument_specs: <bool>        # meta/argument_specs.yml present?
has_molecule_tests: <bool>        # molecule/ folder present?
non_fqcn_task_count: <int>        # tasks using a module WITHOUT FQCN
insecure_download_count: <int>    # http:// (non-TLS) downloads
unguarded_shell_count: <int>      # shell/command without creates:/removes:
ignore_errors_count: <int>        # tasks with ignore_errors: true
secret_in_defaults: <bool>        # plaintext secret in defaults/?
score: <int 0-10>                 # your overall score
verdict: <adopt|fork|reject>      # your argued recommendation
```

### 🧩 Stuck?

```bash
dsoxlab hint galaxy-auditer-role-existant
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

Record in `challenge/solution.sh` the commands used for
the audit (grep, find, possibly ansible-lint...). This log must exist
for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/galaxy/auditer-role-existant/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean galaxy-auditer-role-existant
```

### 💡 Going further

- Run `ansible-lint --profile production vendor/thirdparty_backup/`:
  how many of your findings does it catch on its own? Which ones
  escape it (the secret, the http URL)?
- Audit a real Galaxy role with the same grid and compare.
- Turn the grid into a PR template for your internal reviews.
