# Votre EE a été construit à la main, et il a neuf mois

## La situation

L'EE sur mesure fait tourner toute la production, et il a été construit sur un
portable l'automne dernier. Depuis, son image de base a accumulé des CVE
critiques, personne ne l'a reconstruit parce que personne n'en est propriétaire,
et personne ne peut prouver que l'image du registre est bien celle qui a été
construite : elle a été poussée depuis un poste avec un token personnel. Un
artefact qui fait tourner tout un parc ne peut pas sortir de l'après-midi de
quelqu'un.

Votre mission, depuis le répertoire du projet :

1. Construire l'EE en **CI** plutôt que sur un poste, pour qu'un rebuild soit à un
   commit de distance et que l'horloge des CVE cesse de tourner sans surveillance.
2. **Scanner l'image et bloquer dessus** : un build qui trouve des vulnérabilités
   hautes ou critiques doit faire échouer le pipeline, pas prévenir dans un log
   que personne ne lit.
3. **Signer l'image** en keyless, pour que les consommateurs vérifient que
   l'artefact vient de votre pipeline et non d'un poste, puis la publier.
4. Durcir le pipeline lui-même : **épingler les actions tierces par SHA de
   commit**, garder des permissions globales vides et n'accorder à chaque job que
   son strict nécessaire, sans laisser d'identifiants derrière le checkout.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/exec-playbook/#pipeline-github-actions

## 🎯 Challenge — Pipeline CI complet pour builder + signer un EE

### ✅ Objectif

Écrire 2 pipelines CI (GitHub Actions + GitLab CI) qui buildent,
scannent et signent un EE de production. Les deux fichiers sont livrés en
**squelette** (des `???`) : c'est vous qui écrivez chaque étape.

| Fichier | Attente |
| --- | --- |
| `.github/workflows/build-ee.yml` | Actions externes épinglées par **SHA 40 caractères**. `permissions: {}` au global, réélargies dans le job (dont `id-token: write` pour cosign). `persist-credentials: false`. Scan **Trivy** avec `exit-code: '1'`. **Signature `cosign`**. |
| `.gitlab-ci.yml` | 4 stages `build`, `scan`, `push`, `sign`, avec un job par stage. |
| `execution-environment.yml` | Livré. Doit déclarer `version: 3` (schéma builder v3). |

### 🧩 Bloqué ?

```bash
dsoxlab hint ee-ci-pipeline
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

Le pipeline tourne sur PR / tag, pas localement. Validez au moins le
workflow GitHub avec `actionlint .github/workflows/build-ee.yml` : pytest
le lance aussi si le binaire est présent.

### 📓 Journal de commandes

Quand vos deux pipelines sont prêts, consignez dans `challenge/solution.sh`
les commandes utilisées (recherche des SHA via `gh api`, run `actionlint`).
Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/ci-pipeline/challenge/tests/
```

Le test valide la **sémantique** des deux fichiers CI (épinglage SHA,
permissions, Trivy bloquant, cosign, 4 stages) et exécute actionlint si
disponible.

### 🧹 Reset

```bash
dsoxlab clean ee-ci-pipeline
```

### 💡 Pour aller plus loin

- **Renovate / Dependabot** : auto-update des SHA pinnés (avec PR).
- **Reusable workflows** : factoriser le build EE entre plusieurs repos.
- **Vault des secrets `cosign`** : preferer la signature **keyless OIDC**
  (pas de clé privée à manipuler).
- **Provenance SLSA-3** : ajouter `actions/attest-build-provenance` pour
  l'attestation SLSA.
