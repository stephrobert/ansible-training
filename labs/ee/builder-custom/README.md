# Lab 86 — Construire son propre EE avec ansible-builder

> 💡 **Pré-requis** :
> - **Podman** installé (`podman --version`).
> - **ansible-builder** ≥ 3.1.0 : `pipx install ansible-builder`.
> - Optionnel : **ansible-navigator** pour tester l'EE construit.

## 🧠 Rappel

🔗 [**Construire un EE avec ansible-builder**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/ee-builder/)

**`ansible-builder`** v3 lit un fichier **`execution-environment.yml`** v3 et génère un **`Containerfile`** multi-stage qui produit l'image OCI finale via **Podman**. Quatre fichiers cohabitent :

- **`execution-environment.yml`** : recette (version, base image, deps, build steps).
- **`requirements.yml`** : collections Ansible (Galaxy).
- **`requirements.txt`** : dépendances Python (pip).
- **`bindep.txt`** : dépendances système (dnf/apt selon la base).

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un **`execution-environment.yml`** schéma v3.
2. Pinner les **versions** : ansible-core, collections, Python deps, system deps.
3. Lancer **`ansible-builder build`** avec Podman.
4. Inspecter le **`Containerfile`** généré dans `./context/`.
5. Tester l'EE construit avec **`ansible-navigator`**.
6. Pousser l'EE sur un registre privé (Quay, Harbor, GitLab Registry).

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/ee/builder-custom/

# Vérifier ansible-builder
ansible-builder --version
# → 3.1.0 ou supérieur attendu

# Build l'EE
./build-ee.sh
```

## ⚙️ Arborescence

```text
labs/ee/builder-custom/
├── README.md
├── build-ee.sh                      ← lance ansible-builder
├── execution-environment.yml        ← recette v3
├── requirements.yml                 ← collections Ansible pinnées
├── requirements.txt                 ← deps Python pinnées
├── bindep.txt                       ← deps système (dnf)
├── configs/
│   └── ansible.cfg                  ← config injectée dans l'EE
├── context/                         ← (généré par ansible-builder)
│   └── Containerfile
└── challenge/
    └── tests/
        └── test_ee_builder.py       ← 9 tests structurels
```

## 📚 Exercice 1 — Inspecter execution-environment.yml v3

```yaml
version: 3                                    # ← OBLIGATOIRE en 2026

images:
  base_image:
    name: quay.io/ansible/community-ee-minimal:latest

dependencies:
  ansible_core:
    package_pip: ansible-core==2.18.1         # pinning strict
  ansible_runner:
    package_pip: ansible-runner==2.4.1
  galaxy: requirements.yml                    # collections
  python: requirements.txt                    # pip
  system: bindep.txt                          # dnf

additional_build_files:
  - src: configs/ansible.cfg
    dest: configs

additional_build_steps:
  prepend_base:
    - RUN echo "Build $(date)" > /etc/ee-build-info
  append_final:
    - COPY _build/configs/ansible.cfg /etc/ansible/ansible.cfg
```

🔍 **Observation** : `version: 3` est **obligatoire**. Sans, ansible-builder lit en mode v1 hérité et **ignore** `dependencies.ansible_core` — source de bug classique.

## 📚 Exercice 2 — Build avec Podman

```bash
ansible-builder build \
  --tag localhost/lab86-my-ee:1.0.0 \
  --container-runtime podman \
  --file execution-environment.yml \
  --context ./context \
  --verbosity 2
```

Sortie typique :

```text
[1/3] Resolving collections via Galaxy...
[2/3] Building intermediate image (galaxy stage)...
[3/3] Building final image...
Successfully tagged localhost/lab86-my-ee:1.0.0
```

🔍 **Observation** : ansible-builder génère **`./context/Containerfile`** multi-stage (4 stages : base, galaxy, builder, final). Inspectez-le pour comprendre.

## 📚 Exercice 3 — Vérifier l'EE construit

```bash
podman images | grep lab86

# ansible-core embarqué
podman run --rm localhost/lab86-my-ee:1.0.0 ansible --version | head -1
# → ansible [core 2.18.1]

# collections embarquées
podman run --rm localhost/lab86-my-ee:1.0.0 ansible-galaxy collection list
```

Sortie attendue :

```text
ansible.builtin            2.18.1
ansible.posix              2.0.0
community.general          10.5.0
kubernetes.core            5.1.1
```

🔍 **Observation** : seules les collections **explicitement déclarées** dans `requirements.yml` (+ `ansible.builtin` automatique) sont présentes. Pas de bloat — c'est le bénéfice de partir d'une `community-ee-minimal`.

## 📚 Exercice 4 — Tester l'EE avec ansible-navigator

```bash
# Créer un playbook minimal
cat > test.yml <<'EOF'
---
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Vérifier kubernetes.core
      ansible.builtin.debug:
        msg: "kubernetes.core OK"
EOF

# Lancer dans l'EE custom
ansible-navigator run test.yml \
  --eei localhost/lab86-my-ee:1.0.0 \
  -m stdout
```

🔍 **Observation** : navigator lance Podman avec votre EE custom — pas avec creator-ee. Vous **maîtrisez** ce qui s'exécute, **ligne par ligne** dans `execution-environment.yml`.

## 📚 Exercice 5 — Pinning rigoureux et reproductibilité

Comparez :

| Pratique | Effet |
|----------|-------|
| `ansible-core: ansible-core` | Récupère la dernière au build → non reproductible. |
| `ansible-core==2.18.1` | Toujours 2.18.1. **Reproductible**. |
| `community.general` (sans version) | Dernière au moment du build. |
| `community.general 10.5.0` | Version exacte. **Recommandé**. |

🔍 **Observation cruciale** : **2026, on pinne tout**. Une image rebuild dans 6 mois doit donner **bit-pour-bit le même résultat** — sinon le bénéfice "fige le runtime" est annulé.

## 📚 Exercice 6 — Pousser sur un registre privé

```bash
# Tag pour Quay
podman tag localhost/lab86-my-ee:1.0.0 quay.io/myorg/my-ee:1.0.0

# Login
podman login quay.io

# Push
podman push quay.io/myorg/my-ee:1.0.0
```

🔍 **Observation** : pattern semver — toujours pousser `:1.0.0` (tag patch immuable), puis `:1.0` (mineur), `:1` (majeur), et un `:latest` qui suit le dernier stable. **Jamais écraser** un tag patch publié.

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible votre poste local + un EE OCI custom ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi pinner `ansible-core==2.18.1` plutôt que `>=2.18`?

2. Que produit `ansible-builder build --no-cache` et quand l'utiliser ?

3. Comment **scanner** l'EE construit pour détecter des CVEs ? (Indice : `trivy image`).

4. Comment **signer** l'image avec **cosign** avant push ? Pourquoi ?

## 🚀 Challenge final

Le challenge ([`challenge/tests/`](challenge/tests/)) valide via 9 tests pytest :

- Schéma v3 du fichier `execution-environment.yml`.
- Pinning de toutes les dépendances (collections, Python, system).
- Profil `[platform:rpm]` dans `bindep.txt`.
- Script de build utilise Podman + ansible-builder.

```bash
LAB_NO_REPLAY=1 pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Lab 87** : pipeline CI qui build, scan Trivy, push sur registre.
- **Lab 88** : debug d'un EE cassé (collection manquante, deps incompatible).
- **`ansible-builder create`** (sans build) : génère seulement le Containerfile.
- **`additional_build_steps`** avancé : injecter certificats CA, config kerberos, plugins custom.
- **Multi-arch** : `podman buildx` pour produire amd64 + arm64.

## 🔍 Sécurité — bonnes pratiques 2026

- **Pin strict** sur **toutes** les couches (ansible-core, collections, Python, system).
- **Base image pinnée par digest** : `community-ee-minimal@sha256:abc...` (pas `:latest`).
- **Trivy scan** dans la CI : `trivy image --severity HIGH,CRITICAL --exit-code 1 my-ee:1.0.0`.
- **SBOM** : `syft my-ee:1.0.0 -o spdx-json > sbom.json`.
- **Cosign sign** avant push prod : `cosign sign quay.io/myorg/my-ee:1.0.0`.
- **Registre privé** + auth (pas de `:latest` public en prod).

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/ee/builder-custom/lab.yml
ansible-lint labs/ee/builder-custom/challenge/solution.yml
ansible-lint --profile production labs/ee/builder-custom/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
