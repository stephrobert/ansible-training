# Lab 87 — CI/CD pipeline for Execution Environments

> 💡 **Prerequisites**:
> - Lab 86 completed (you know how to build an EE locally).
> - GitHub or GitLab account to run the pipeline.
> - Access to an OCI registry: **GHCR** (free with GitHub) or **GitLab Registry**.

## 🧠 Recap

🔗 [**CI EE pipeline: build, scan, sign, push**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/exec-playbook/#pipeline-github-actions)

An EE in production must be **rebuilt regularly** (deps CVEs), **scanned** (Trivy), **signed** (cosign / Sigstore) and **published** to a private registry. This lab provides **two equivalent pipelines**: **GitHub Actions** and **GitLab CI**, in 2026 mode (SHA pinning, minimal permissions, blocking scan mode).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Build** an EE in a pipeline with **`ansible-builder`**.
2. **Scan** the image with **Trivy** in blocking mode (`exit-code: 1` on HIGH/CRITICAL).
3. **Push** to **GHCR** (GitHub) or **GitLab Registry**.
4. **Sign** the image with **cosign keyless** (Sigstore + OIDC).
5. **Pin** GitHub actions by **SHA** (zizmor compatible).
6. Configure **`permissions: {}`** + **`persist-credentials: false`** (supply-chain hardening).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/ee/ci-pipeline/

# Check the pipeline files
ls -la .github/workflows/build-ee.yml .gitlab-ci.yml

# Local lint (optional)
zizmor .github/workflows/build-ee.yml
```

## ⚙️ Tree

```text
labs/ee/ci-pipeline/
├── README.md
├── execution-environment.yml
├── requirements.yml
├── requirements.txt
├── bindep.txt
├── .github/
│   └── workflows/
│       └── build-ee.yml             ← GitHub Actions pipeline
├── .gitlab-ci.yml                   ← GitLab CI pipeline
└── challenge/
    └── tests/
        └── test_ee_ci.py            ← 11 structural tests
```

## 📚 Exercise 1 — GitHub Actions pipeline

The [`.github/workflows/build-ee.yml`](.github/workflows/build-ee.yml) workflow does 4 steps:

1. **Build** with `ansible-builder build --tag $SHA --tag latest`.
2. **Trivy scan**: `severity HIGH,CRITICAL`, `exit-code: 1` (blocks the pipeline).
3. **Push** to GHCR (`ghcr.io/<owner>/lab87-ee:<sha>`).
4. **cosign sign** (keyless OIDC, without a local key).

🔍 **Visible 2026 best practices**:

- **`uses:` pinned by SHA** (40 hex chars), not by tag: protects against tag mutation.
- **`permissions: {}`** at the workflow level, elevated permissions **only** in the jobs that need them.
- **`persist-credentials: false`** on `actions/checkout`: blocks use of the Git token after checkout.
- **`id-token: write`** only for the job that signs with cosign keyless.

## 📚 Exercise 2 — Equivalent GitLab CI pipeline

The [`.gitlab-ci.yml`](.gitlab-ci.yml) file does the **4 same steps**:

```yaml
stages:
  - build       # ansible-builder in image quay.io/ansible/ansible-builder:3.1.0
  - scan        # trivy in image aquasec/trivy:0.59.1
  - push        # podman in image quay.io/podman/stable
  - sign        # cosign in image gcr.io/projectsigstore/cosign:v2.4.1
```

Difference: GitLab CI uses the automatic `$CI_REGISTRY_IMAGE`, whereas GHCR requires the full URL `ghcr.io/<owner>/<repo>`.

## 📚 Exercise 3 — Run the Trivy scan locally

Before pushing the code to CI, scan locally:

```bash
# Local build
ansible-builder build --tag local/lab87-ee:dev --container-runtime podman \
  --file execution-environment.yml --context ./context

# Scan
trivy image --severity HIGH,CRITICAL local/lab87-ee:dev
```

🔍 **Observation**: Trivy detects CVEs **in the image layers** (system packages + Python deps). If a HIGH CVE appears, the CI build fails. Solution: bump the pinned version of the vulnerable package.

## 📚 Exercise 4 — cosign keyless signature

```bash
# Locally (requires COSIGN_EXPERIMENTAL=1 on older versions)
cosign sign --yes ghcr.io/myorg/lab87-ee:abc123

# Verify the signature
cosign verify ghcr.io/myorg/lab87-ee:abc123 \
  --certificate-identity-regexp 'https://github.com/.+/lab87' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

🔍 **Observation**: **keyless** = no private key to manage. cosign uses the GitHub/GitLab runner's OIDC token to authenticate with Sigstore (`fulcio.sigstore.dev`). The signature is publicly attested in **Rekor** (transparency log).

## 📚 Exercise 5 — Pull policy in Podman

To require **signed** images on the production machine:

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

🔍 **Observation**: without this policy, anyone pushes an image with the right name and it is run. With the policy, **only images signed by your org's OIDC** are allowed.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  compliant with best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name. `ansible-lint --profile
  production` checks it.
- **Targeting convention**: this lab targets your local machine + an OCI image built by CI. To adapt it to
  another group, adjust `hosts:` in `lab.yml`/`solution.yml` then rerun.
- **Isolated reset**: `dsoxlab clean <lab-id>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why pin GitHub actions by **SHA** rather than by tag `@v4.2.2`?

2. What does **`persist-credentials: false`** do on `actions/checkout`? What risk does it avoid?

3. **Trivy** returns `exit-code: 1` on a HIGH CVE of a package you **cannot** fix (no patch available). How do you react?

4. **Cosign keyless vs with a key**: which threat model does each favor?

## 🚀 Final challenge

The challenge ([`challenge/tests/`](challenge/tests/)) validates through **11 pytest tests**:

- GitHub workflow present + actions pinned by SHA.
- `permissions: {}` + `persist-credentials: false`.
- Blocking Trivy scan + cosign signature.
- Equivalent 4-stage GitLab CI pipeline.
- `execution-environment.yml` v3 schema.

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Going further

- **Lab 88**: debug a broken EE in CI.
- **Renovate**: bot that opens PRs to bump `ansible-core==2.18.1` -> 2.19.0 automatically.
- **OPA / Conftest**: validate `execution-environment.yml` with policies (no `:latest`, no missing version).
- **AAP Controller**: import the EE from the signed registry via the UI.
- **Multi-arch**: `--platform linux/amd64,linux/arm64` for ARM Macs.

## 🔍 Security — 2026 best practices

- **Trivy in blocking mode**: `exit-code: 1` on HIGH/CRITICAL.
- **`persist-credentials: false`** systematically on `actions/checkout`.
- **`permissions: {}`** at the workflow, elevated permissions **only** in the jobs that need them.
- **Cosign signature** + Rekor transparency log.
- **Renovate** to bump the pinnings automatically (PR-driven).
- **zizmor + poutine** mandatory lints on the pipelines.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/ee/ci-pipeline/lab.yml
ansible-lint labs/ee/ci-pipeline/challenge/solution.yml
ansible-lint --profile production labs/ee/ci-pipeline/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
