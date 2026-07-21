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

## 🧩 Hints

- Annotated tag: `git tag -a v1.2.0 -m "Release v1.2.0"` (a lightweight tag will
  not pass: `git cat-file -t` must answer `tag`).
- In a script, set the local Git identity of the working repo:
  `git -C ... config user.email/user.name` before committing.
- `ansible-galaxy collection init acme.webstack --init-path ...` lays down a
  `galaxy.yml` whose `version:` you adjust (sed, or edit then copy).
- The tag / CHANGELOG / galaxy.yml consistency is exactly what a
  reviewer checks before authorizing a publication.

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
