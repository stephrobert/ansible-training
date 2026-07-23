# 🎯 Challenge: bring a role up to the production profile

## ✅ Mission

The `roles/webserver` role is delivered **deliberately faulty**: it
works, but `ansible-lint --profile production` flags a good dozen
violations there (missing FQCN, unnamed task, risky octal mode,
`ignore_errors`, `shell` instead of a module...). The lint configuration
files are delivered as skeletons.

Your work, in two steps:

1. **Write the configuration**: `.ansible-lint` (production profile,
   exclusions), `.yamllint` (strict truthy), `.pre-commit-config.yaml`
   (base hooks + yamllint + ansible-lint).
2. **Fix the role** until `ansible-lint --profile production roles/`
   returns 0, **without changing its behavior** (same packages, same
   service, same deployed page).

Pytest actually runs `ansible-lint --profile production`: the lab
is validated only when the linter is green.

## 🧩 Stuck?

```bash
dsoxlab hint tests-ansible-lint-production
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 📓 Command log

When everything is green, record the commands you ran (`ansible-lint ...`,
`yamllint roles/`, `pre-commit run --all-files`) in `challenge/solution.sh`.
This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/tests/ansible-lint-production/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean tests-ansible-lint-production
```

## 💡 Going further

- `pre-commit install`: make committing impossible while the lint fails.
- `ansible-lint --fix`: automatic fixes (review before commit).
- Wire this same profile into the CI from lab 69.
