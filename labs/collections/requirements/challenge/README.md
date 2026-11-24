# A supply-chain audit lands on your project

## The situation

The security team is sweeping every automation repository after a compromised
package hit another department. The question they ask yours is short: for each
collection you install, where does it come from, which exact version, and how do
you know the bytes you received are the bytes the publisher signed? Right now the
honest answer is that some come from public Galaxy, one is cloned from a Git
branch that moves, and nobody has ever verified anything.

Your mission, from **control-node.lab**:

1. Declare every collection the project needs in one manifest, spanning several
   **kinds of source**: public Galaxy, a Git repository, and at least one more,
   each with its type made explicit.
2. **Pin strictly**: an exact version or an immutable Git tag. A moving branch is
   not a dependency, it is a promise someone else can break.
3. Install them into a **project-local path** rather than the user's home, so the
   environment is reproducible and disposable, and prove on **db1.lab** what was
   really installed.
4. Verify the integrity of what came down, and be ready to pull from more than one
   Galaxy server when the company puts a private hub in front of the public one.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/requirements-yml/ (in French)

## 🎯 Challenge — Multi-source `requirements.yml`

### ✅ Objective

Write a **`requirements.yml`** that combines **3 different sources**, install it into `local_collections/`, and deposit the list of installed collections on `db1.lab`.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab94-collections.txt` |
| Permissions | `0644`, owner `root` |
| Number of installed collections | **≥ 3** |
| Required sources | Galaxy + Git + (URL **or** dir) |
| Pinning | **Strict** (semver `version: "X.Y.Z"` or Git tag) |

### 🧩 Stuck?

```bash
dsoxlab hint collections-requirements
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/collections/requirements/challenge/tests/
```

The pytest test validates:

- `/tmp/lab94-collections.txt` exists with mode `0644` and owner `root`.
- At least 3 collections listed in the file.
- At least one collection with an FQCN (dot in the namespace).

### 🧹 Reset

```bash
dsoxlab clean collections-requirements
```

### 💡 Going further

- **GPG signatures**: add `signatures:` to a collection + `--keyring` at launch.
- **Renovate**: configure a bot to auto-bump `version: "X.Y.Z"` on each upstream release.
- **`ansible-lint --profile production`**: zero warning expected.
