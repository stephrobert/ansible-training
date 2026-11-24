# The review that keeps having the same argument

## The situation

Every pull request on the team's roles reopens the same debate: bare module
names, unnamed tasks, a `shell:` where a dedicated module exists, `yes` instead
of `true`. The reviewers are tired of being a linter. Then last month someone
committed a private key, and it sat in the history for three days before anyone
noticed. Style is negotiable in a review; a leaked key is not. Both belong to a
machine, and the machine should say no before the commit exists.

Your mission, from the project directory:

1. Pin the linter to its **strictest profile**, the one expected of code that
   ships to production, and see what it says about the role as it stands.
2. Add a strict YAML policy on top: the ambiguous booleans and the sloppy
   formatting stop passing review because they stop passing the tool.
3. Wire both into a **Git hook** that runs on every commit, so non-conforming
   code never reaches the branch, and CI merely confirms what you already know.
4. Add a hook that **blocks secret leaks** at commit time, private keys included.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ansible-lint-production-profile/ (in French)

## 🎯 Challenge: bring a role up to the production profile

### ✅ Mission

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

### 🧩 Stuck?

```bash
dsoxlab hint tests-ansible-lint-production
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

When everything is green, record the commands you ran (`ansible-lint ...`,
`yamllint roles/`, `pre-commit run --all-files`) in `challenge/solution.sh`.
This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/tests/ansible-lint-production/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean tests-ansible-lint-production
```

### 💡 Going further

- `pre-commit install`: make committing impossible while the lint fails.
- `ansible-lint --fix`: automatic fixes (review before commit).
- Wire this same profile into the CI from lab 69.
