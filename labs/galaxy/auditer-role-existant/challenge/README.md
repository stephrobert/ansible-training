# 🎯 Challenge: audit a real third-party role, verified conclusions

## ✅ Mission

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

## 🧩 Hints

- Go through each file of the role: `tasks/`, `defaults/`, `meta/`,
  and note what is missing as much as what is present.
- A module without a dot in its name (`yum:` instead of
  `ansible.builtin.yum:`) is not FQCN.
- A `shell:`/`command:` without `creates:` or `removes:` breaks
  idempotence: count them.
- A password in `defaults/main.yml` ends up in the Git of every
  consumer of the role: it is disqualifying in production.
- The scale is yours, but remember the grid in
  `AUDIT_CHECKLIST.md`: plaintext secret + zero tests, the conclusion is
  not up for debate.

## 📓 Command log

Record in `challenge/solution.sh` the commands used for
the audit (grep, find, possibly ansible-lint...). This log must exist
for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/auditer-role-existant/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean galaxy-auditer-role-existant
```

## 💡 Going further

- Run `ansible-lint --profile production vendor/thirdparty_backup/`:
  how many of your findings does it catch on its own? Which ones
  escape it (the secret, the http URL)?
- Audit a real Galaxy role with the same grid and compare.
- Turn the grid into a PR template for your internal reviews.
