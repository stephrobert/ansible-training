# 🎯 Challenge: version and prepare a publication, for real

## ✅ Mission

No more versioning on paper: you write a
`challenge/solution.sh` script that **practices** the release workflow in
`challenge/work/`, and pytest **runs your script** then checks the
Git state and the produced artifacts. Everything is local, no Galaxy account required.

Your script, launched from the lab root, must build:

| Expected effect | Detail |
| --- | --- |
| `challenge/work/repo/` | an initialized Git repo containing the `webserver` role (copied from `roles/`) and a `CHANGELOG.md`, all committed |
| `CHANGELOG.md` | Keep a Changelog format: at least 2 versions `[X.Y.Z]`, an `### Added` section, and `### Changed` or `### Fixed` |
| Git tag | an **annotated** tag `vX.Y.Z` whose version matches the **last** entry of the CHANGELOG |
| `challenge/work/dist/` | the archive of an `acme.webstack` collection built with `ansible-galaxy collection build`, whose `galaxy.yml` version is **the same** as the tag |

Constraints:

- **Replayable** script: pytest deletes `challenge/work/` before
  running it, your script recreates everything.
- `set -euo pipefail` at the top.
- The CHANGELOG content is yours: describe real changes of the
  webserver role (pytest checks the format and the version consistency,
  not the prose).

## 🧩 Stuck?

```bash
dsoxlab hint galaxy-versionner-publier
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧪 Validation

```bash
chmod +x challenge/solution.sh
pytest -v labs/galaxy/versionner-publier/challenge/tests/
```

Pytest runs your script, actually queries Git (`git tag`,
`git cat-file`, `git log`) and checks the built archive.

## 🧹 Reset

```bash
dsoxlab clean galaxy-versionner-publier
```

## 💡 Going further

- `PUBLISH.md` (at the lab root): the complete Galaxy publication
  procedure, GitHub webhook included.
- `towncrier`: generate the CHANGELOG from PR fragments.
- GitHub workflow `on: push: tags: ['v*']` that publishes to Galaxy (lab 69).
