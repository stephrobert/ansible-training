# Lab 87 — Pipeline CI/CD pour Execution Environments

> 💡 **Pré-requis** :
> - Lab 86 validé (vous savez builder un EE localement).
> - Compte GitHub ou GitLab pour exécuter le pipeline.
> - Accès à un registre OCI : **GHCR** (gratuit avec GitHub) ou **GitLab Registry**.

## 🧠 Rappel

🔗 [**Pipeline CI EE — build, scan, sign, push**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/exec-playbook/#cicd)

Un EE en production doit être **rebuildé régulièrement** (CVEs des deps), **scanné** (Trivy), **signé** (cosign / Sigstore) et **publié** sur un registre privé. Ce lab fournit **deux pipelines équivalents** : **GitHub Actions** et **GitLab CI**, en mode 2026 (SHA pinning, permissions minimales, scan en mode bloquant).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Builder** un EE dans un pipeline avec **`ansible-builder`**.
2. **Scanner** l'image avec **Trivy** en mode bloquant (`exit-code: 1` sur HIGH/CRITICAL).
3. **Pousser** vers **GHCR** (GitHub) ou **GitLab Registry**.
4. **Signer** l'image avec **cosign keyless** (Sigstore + OIDC).
5. **Pinner** les actions GitHub par **SHA** (zizmor compatible).
6. Configurer **`permissions: {}`** + **`persist-credentials: false`** (durcissement supply-chain).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/ee/ci-pipeline/

# Vérifier les fichiers du pipeline
ls -la .github/workflows/build-ee.yml .gitlab-ci.yml

# Lint local (optionnel)
zizmor .github/workflows/build-ee.yml
```

## ⚙️ Arborescence

```text
labs/ee/ci-pipeline/
├── README.md
├── execution-environment.yml
├── requirements.yml
├── requirements.txt
├── bindep.txt
├── .github/
│   └── workflows/
│       └── build-ee.yml             ← pipeline GitHub Actions
├── .gitlab-ci.yml                   ← pipeline GitLab CI
└── challenge/
    └── tests/
        └── test_ee_ci.py            ← 8 tests structurels
```

## 📚 Exercice 1 — Pipeline GitHub Actions

Le workflow [`.github/workflows/build-ee.yml`](.github/workflows/build-ee.yml) fait 4 étapes :

1. **Build** avec `ansible-builder build --tag $SHA --tag latest`.
2. **Scan Trivy** : `severity HIGH,CRITICAL`, `exit-code: 1` (bloque le pipeline).
3. **Push** vers GHCR (`ghcr.io/<owner>/lab87-ee:<sha>`).
4. **Sign cosign** (keyless OIDC, sans clé locale).

🔍 **Bonnes pratiques 2026 visibles** :

- **`uses:` pinné par SHA** (40 chars hex), pas par tag — protège contre tag mutation.
- **`permissions: {}`** au niveau workflow, permissions élevées **uniquement** dans les jobs qui en ont besoin.
- **`persist-credentials: false`** sur `actions/checkout` — bloque l'usage du token Git après le checkout.
- **`id-token: write`** uniquement pour le job qui signe avec cosign keyless.

## 📚 Exercice 2 — Pipeline GitLab CI équivalent

Le fichier [`.gitlab-ci.yml`](.gitlab-ci.yml) fait les **4 mêmes étapes** :

```yaml
stages:
  - build       # ansible-builder dans image quay.io/ansible/ansible-builder:3.1.0
  - scan        # trivy en image aquasec/trivy:0.59.1
  - push        # podman dans image quay.io/podman/stable
  - sign        # cosign dans image gcr.io/projectsigstore/cosign:v2.4.1
```

Différence : GitLab CI utilise `$CI_REGISTRY_IMAGE` automatique, alors que GHCR demande l'URL complète `ghcr.io/<owner>/<repo>`.

## 📚 Exercice 3 — Lancer le scan Trivy localement

Avant de pousser le code en CI, scannez localement :

```bash
# Build local
ansible-builder build --tag local/lab87-ee:dev --container-runtime podman \
  --file execution-environment.yml --context ./context

# Scan
trivy image --severity HIGH,CRITICAL local/lab87-ee:dev
```

🔍 **Observation** : Trivy détecte les CVEs **dans les couches de l'image** (system packages + Python deps). Si une CVE HIGH apparaît, le build CI échoue. Solution : bumper la version pinnée du package vulnérable.

## 📚 Exercice 4 — Signature cosign keyless

```bash
# En local (nécessite COSIGN_EXPERIMENTAL=1 sur anciennes versions)
cosign sign --yes ghcr.io/myorg/lab87-ee:abc123

# Vérifier la signature
cosign verify ghcr.io/myorg/lab87-ee:abc123 \
  --certificate-identity-regexp 'https://github.com/.+/lab87' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

🔍 **Observation** : **keyless** = pas de clé privée à gérer. cosign utilise l'OIDC token du runner GitHub/GitLab pour s'authentifier auprès de Sigstore (`fulcio.sigstore.dev`). La signature est attestée publiquement dans **Rekor** (transparence log).

## 📚 Exercice 5 — Politique de pull dans Podman

Pour exiger des images **signées** sur le poste de prod :

```toml
# /etc/containers/policy.json
{
  "default": [{"type": "reject"}],
  "transports": {
    "docker": {
      "ghcr.io/myorg/lab87-ee": [{
        "type": "sigstoreSigned",
        "fulcioCAData": "...",
        "rekorPublicKeyData": "...",
        "signedIdentity": {"type": "remapIdentity"}
      }]
    }
  }
}
```

🔍 **Observation** : sans cette policy, n'importe qui pousse une image avec le bon nom et elle est exécutée. Avec la policy, **seules les images signées par votre OIDC d'org** sont autorisées.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible votre poste local + une image OCI buildée par CI ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi pinner les actions GitHub par **SHA** plutôt que par tag `@v4.2.2` ?

2. Que fait **`persist-credentials: false`** sur `actions/checkout` ? Quel risque évite-t-il ?

3. **Trivy** retourne `exit-code: 1` sur une CVE HIGH d'un package que vous **ne pouvez pas** corriger (pas de patch disponible). Comment réagir ?

4. **Cosign keyless vs avec clé** : quel modèle de menace privilégie l'un ou l'autre ?

## 🚀 Challenge final

Le challenge ([`challenge/tests/`](challenge/tests/)) valide via **8 tests pytest** :

- Workflow GitHub présent + actions pinnées par SHA.
- `permissions: {}` + `persist-credentials: false`.
- Trivy scan bloquant + signature cosign.
- Pipeline GitLab CI à 4 stages équivalents.
- `execution-environment.yml` schéma v3.

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Lab 88** : debug d'un EE cassé en CI.
- **Renovate** : bot qui ouvre des PR pour bumper `ansible-core==2.18.1` → 2.19.0 automatiquement.
- **OPA / Conftest** : valider `execution-environment.yml` avec des policies (pas de `:latest`, pas de version manquante).
- **AAP Controller** : importer l'EE depuis le registre signé via le UI.
- **Multi-arch** : `--platform linux/amd64,linux/arm64` pour ARM Macs.

## 🔍 Sécurité — bonnes pratiques 2026

- **Trivy en mode bloquant** : `exit-code: 1` sur HIGH/CRITICAL.
- **`persist-credentials: false`** systématiquement sur `actions/checkout`.
- **`permissions: {}`** au workflow, permissions élevées **uniquement** dans les jobs qui en ont besoin.
- **Cosign signature** + Rekor transparency log.
- **Renovate** pour bumper les pinning automatiquement (PR-driven).
- **zizmor + poutine** lints obligatoires sur les pipelines.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/ee/ci-pipeline/lab.yml
ansible-lint labs/ee/ci-pipeline/challenge/solution.yml
ansible-lint --profile production labs/ee/ci-pipeline/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
