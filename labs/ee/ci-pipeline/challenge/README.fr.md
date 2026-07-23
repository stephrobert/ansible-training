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

## 🧩 Bloqué ?

```bash
dsoxlab hint ee-ci-pipeline
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

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
