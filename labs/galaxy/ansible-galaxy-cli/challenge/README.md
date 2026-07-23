# 🎯 Challenge: really driving the `ansible-galaxy` CLI

## ✅ Mission

No more reading the cheatsheet: you write a
`challenge/solution.sh` script that **runs** the `ansible-galaxy` commands,
and pytest **runs your script** then checks the effects on disk.
Everything happens offline (scaffolding, build and install from a local
archive), no Galaxy account is needed.

Your script, launched from the lab root, must produce in
`challenge/build/`:

| Expected effect | Command family |
| --- | --- |
| A `demo_web` role scaffolded in `challenge/build/roles/` | `ansible-galaxy role init` |
| An `acme.tools` collection scaffolded in `challenge/build/collections/` | `ansible-galaxy collection init` |
| The collection archive in `challenge/build/dist/` | `ansible-galaxy collection build` |
| The collection installed in `challenge/build/installed/` **from the local archive** | `ansible-galaxy collection install` |
| The collection visible to `ansible-galaxy collection list -p challenge/build/installed` | `ansible-galaxy collection list` |

Constraints:

- The script must be **replayable**: pytest deletes `challenge/build/`
  before running it, your script recreates everything on each run.
- `set -euo pipefail` at the top: the slightest failing command must make
  the script fail.

## 🧩 Stuck?

```bash
dsoxlab hint galaxy-ansible-galaxy-cli
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧪 Validation

```bash
chmod +x challenge/solution.sh
pytest -v labs/galaxy/ansible-galaxy-cli/challenge/tests/
```

Pytest runs `challenge/solution.sh` then checks each effect
(role structure, galaxy.yml, archive, MANIFEST.json of the installed
collection, output of `collection list`).

## 🧹 Reset

```bash
dsoxlab clean galaxy-ansible-galaxy-cli
```

## 💡 Going further

- `ansible-galaxy collection verify`: compare an installed collection to
  its Galaxy source (requires the network).
- `ANSIBLE_COLLECTIONS_PATH`: point Ansible to your custom
  install folder.
- `ansible-galaxy collection list --format json`: output parsable in CI.
