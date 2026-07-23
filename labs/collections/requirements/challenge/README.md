# 🎯 Challenge — Multi-source `requirements.yml`

## ✅ Objective

Write a **`requirements.yml`** that combines **3 different sources**, install it into `local_collections/`, and deposit the list of installed collections on `db1.lab`.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab94-collections.txt` |
| Permissions | `0644`, owner `root` |
| Number of installed collections | **≥ 3** |
| Required sources | Galaxy + Git + (URL **or** dir) |
| Pinning | **Strict** (semver `version: "X.Y.Z"` or Git tag) |

## 🧩 Stuck?

```bash
dsoxlab hint collections-requirements
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/requirements/challenge/tests/
```

The pytest test validates:

- `/tmp/lab94-collections.txt` exists with mode `0644` and owner `root`.
- At least 3 collections listed in the file.
- At least one collection with an FQCN (dot in the namespace).

## 🧹 Reset

```bash
dsoxlab clean collections-requirements
```

## 💡 Going further

- **GPG signatures**: add `signatures:` to a collection + `--keyring` at launch.
- **Renovate**: configure a bot to auto-bump `version: "X.Y.Z"` on each upstream release.
- **`ansible-lint --profile production`**: zero warning expected.
