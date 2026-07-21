# 🎯 Challenge — Pipeline CI complet pour builder + signer un EE

## ✅ Objectif

Écrire 2 pipelines CI (GitHub Actions + GitLab CI) qui buildent,
scannent et signent un EE de production. Les deux fichiers sont livrés en
**squelette** (des `???`) : c'est vous qui écrivez chaque étape.

| Fichier | Attente |
| --- | --- |
| `.github/workflows/build-ee.yml` | Actions externes épinglées par **SHA 40 caractères**. `permissions: {}` au global, réélargies dans le job (dont `id-token: write` pour cosign). `persist-credentials: false`. Scan **Trivy** avec `exit-code: '1'`. **Signature `cosign`**. |
| `.gitlab-ci.yml` | 4 stages `build`, `scan`, `push`, `sign`, avec un job par stage. |
| `execution-environment.yml` | Livré. Doit déclarer `version: 3` (schéma builder v3). |

## 🧩 Indices

### Squelette GitHub Actions

```yaml
---
name: Build & sign EE

on:
  push:
    tags: ["v*.*.*"]
  pull_request:
    branches: [main]

permissions: {}                            # ← {} obligatoire au global

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write                      # cosign keyless OIDC

    steps:
      - uses: actions/checkout@???        # SHA 40 chars (ex: b4ffde...)
        with:
          persist-credentials: false      # ← obligatoire

      - uses: redhat-actions/podman-login@???
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - run: ansible-builder build --tag ghcr.io/${{ github.repository }}/ee:${{ github.ref_name }}

      - uses: aquasecurity/trivy-action@???
        with:
          image-ref: ghcr.io/${{ github.repository }}/ee:${{ github.ref_name }}
          severity: CRITICAL,HIGH
          exit-code: '1'                  # ← bloquer si vuln HIGH+

      - uses: sigstore/cosign-installer@???
      - run: cosign sign --yes ghcr.io/${{ github.repository }}/ee:${{ github.ref_name }}
```

### Pinning SHA d'une action

```bash
gh api repos/actions/checkout/git/refs/tags/v4.2.2 --jq .object.sha
# → b4ffde65f46336ab88eb53be808477a3936bae11
# Utiliser dans `uses:` au lieu de @v4 (mutable)
```

### Squelette GitLab CI (4 stages)

```yaml
---
stages:
  - build
  - scan
  - push
  - sign

variables:
  EE_IMAGE: $CI_REGISTRY_IMAGE/ee:$CI_COMMIT_TAG

build:
  stage: build
  ???

scan:
  stage: scan
  ???

push:
  stage: push
  ???

sign:
  stage: sign
  ???
```

> 💡 **Pièges** :
>
> - **Pinning par SHA 40 chars** : `actions/checkout@b4ffde6...` (pas
>   `@v4`). Sécurité supply chain — un tag peut être bougé, un SHA non.
> - **`permissions: {}`** au global, élargi par job avec `permissions:
>   { contents: read, packages: write, id-token: write }`. Principe du
>   moindre privilège.
> - **`persist-credentials: false`** sur `actions/checkout` : sinon le
>   token reste en `.git/config` après le checkout (risque de fuite).
> - **`cosign` keyless** : signature OIDC sans clé privée. Nécessite
>   `id-token: write` permission. Plus simple que les clés long-vivantes.
> - **Trivy `exit-code: '1'`** : bloquer le pipeline sur CRITICAL/HIGH.
>   Sans, le scan est cosmétique.

## 🚀 Lancement

Le pipeline tourne sur PR / tag, pas localement. Validez au moins le
workflow GitHub avec `actionlint .github/workflows/build-ee.yml` : pytest
le lance aussi si le binaire est présent.

## 📓 Journal de commandes

Quand vos deux pipelines sont prêts, consignez dans `challenge/solution.sh`
les commandes utilisées (recherche des SHA via `gh api`, run `actionlint`).
Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/ci-pipeline/challenge/tests/
```

Le test valide la **sémantique** des deux fichiers CI (épinglage SHA,
permissions, Trivy bloquant, cosign, 4 stages) et exécute actionlint si
disponible.

## 🧹 Reset

```bash
dsoxlab clean ee-ci-pipeline
```

## 💡 Pour aller plus loin

- **Renovate / Dependabot** : auto-update des SHA pinnés (avec PR).
- **Reusable workflows** : factoriser le build EE entre plusieurs repos.
- **Vault des secrets `cosign`** : preferer la signature **keyless OIDC**
  (pas de clé privée à manipuler).
- **Provenance SLSA-3** : ajouter `actions/attest-build-provenance` pour
  l'attestation SLSA.
