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
(`ssh/id_ed25519`), and the **vault password** (`.vault-pass`).

Four assets are attached to each release:

| Asset | What it is for |
| --- | --- |
| `ansible-training-<version>.tar.gz` | the catalogue itself |
| `….tar.gz.sha256` | integrity, checkable offline |
| `….tar.gz.cosign.bundle` | keyless Cosign signature |
| `provenance.intoto.jsonl` | SLSA provenance, the asset OpenSSF Scorecard's Signed-Releases check looks for |

## Why three jobs, and not one

The workflow is split into **build**, **attest**, **publish**, and that split is
the only thing separating SLSA Build Level 2 from Level 3.

GitHub's documentation puts it in two sentences: "Artifact attestations by
itself provides SLSA v1.0 Build Level 2", and "Reusable workflows can provide
isolation between the build process and the calling workflow, to meet SLSA v1.0
Build Level 3". As long as the job that builds the archive is also the one that
signs its provenance, nothing technically stops the build process from
producing provenance that lies. Level 3 requires the signing to happen out of
its reach.

Hence `.github/workflows/attester.yml`, called as a reusable workflow:

- it is the **only workflow in the repository** granted `attestations: write`;
- it receives **a name and a digest**, never the archive nor the repository: it
  performs no `checkout`;
- the publish job can write the release but **cannot attest**, lacking that
  permission;
- the archive is re-checked against its digest **before** publication, so that
  an artifact altered between two jobs is not published with provenance that
  does not describe it.

Until 2026-10-09 this repository attested from its build job — Level 2 — while
its README displayed the Level 3 badge. The five sibling catalogues had already
moved; this was the one left behind.

## Verifying a release

Integrity and contents:

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

Build provenance. Proves the archive really was produced by this repository's
workflow, and not rebuilt by someone else:

```bash
gh attestation verify ansible-training-<version>.tar.gz \
  --repo stephrobert/ansible-training
```

**The check that establishes Build Level 3** names the signing workflow. It
fails if the provenance was produced anywhere other than the isolated attester
workflow, and it is the one to run on the first release to confirm the chain
holds:

```bash
gh attestation verify ansible-training-<version>.tar.gz \
  --repo stephrobert/ansible-training \
  --signer-workflow stephrobert/ansible-training/.github/workflows/attester.yml
```

Keyless Cosign signature. **Both** certificate flags are mandatory: without
them, `cosign verify-blob` accepts any identity, which empties the verification
of its meaning.

```bash
cosign verify-blob \
  --bundle ansible-training-<version>.tar.gz.cosign.bundle \
  --certificate-identity-regexp "https://github.com/stephrobert/ansible-training/.github/workflows/release.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ansible-training-<version>.tar.gz
```

> **Cosign version trap.** The CI installs **Cosign 3.x**, which writes a new
> bundle format. A local **Cosign 2.x** answers `no signatures found` on a
> perfectly signed archive: the release is not broken, the local tool cannot
> read the format. Check `cosign version` and align it before concluding
> anything.

> Commits and tags are created by a human, never by an assistant.
