# Releasing ansible-training

**Language:** [English](./RELEASING.md) · [Français](./RELEASING.fr.md)

This repository ships **lab content**, not a Python package. A release publishes
a **`tar.gz` bundle** of the lab catalog as a GitHub Release asset: no PyPI, no
wheel, no external artifact registry.

## What a release contains

The `release.yml` workflow builds `ansible-training-<version>.tar.gz` with:

- `labs/`, `meta.yml`, `conftest.py`, `inventory/`, `ansible.cfg`,
  `requirements.yml`, `requirements.txt`
- `solution/`, which stays **ansible-vault encrypted** inside the archive
- the governance documents (`README`, `LICENSE`, `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, `CHANGELOG`)

It **excludes** local steering (`.claude/`, `CLAUDE.md`), generated files
(`.venv/`, `.ansible_facts/`, caches), the **private SSH key**
(`ssh/id_ed25519`), and the **vault password** (`.vault-pass`). A `.sha256`
digest is published next to the archive.

## Cutting a release

1. Update `CHANGELOG.md` and `CHANGELOG.fr.md` (move entries under a new
   version).
2. Make sure `dsoxlab validate-structure` is green locally.
3. Tag and push the tag, which triggers `release.yml`:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. The workflow builds the `tar.gz` and its `.sha256`, then creates the GitHub
   Release with auto-generated notes.

## Verifying a release

```bash
sha256sum -c ansible-training-<version>.tar.gz.sha256
tar tzf ansible-training-<version>.tar.gz | head
```

Worth doing once, after the first bundle: check that no secret leaked into the
archive.

```bash
tar tzf ansible-training-<version>.tar.gz | grep -E 'vault-pass|id_ed25519$' \
  && echo "LEAK: do not publish" || echo "OK"
```

> Commits and tags are created by a human, never by an assistant.
