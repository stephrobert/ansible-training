# 🎯 Challenge — Diagnostiquer + corriger un EE cassé

## ✅ Objectif

Le lab livre des fichiers **buggy** à la racine. Votre mission :
identifier les 4 bugs et déposer une **version corrigée** dans
`challenge/`.

| Fichier buggy (racine) | Bug volontaire |
| --- | --- |
| `execution-environment-buggy.yml` | Pas de `version: 3` (schéma manquant) |
| `requirements-buggy.yml` | Collection `community.does-not-exist` (FQCN invalide) |
| `requirements-buggy.txt` | `kubernetes==9999.0.0` (version PyPI inexistante) |
| (système) | Pas de `bindep.txt` (system deps oubliés) |

| Fichier corrigé attendu | Attente |
| --- | --- |
| `challenge/execution-environment.yml` | `version: 3` présent |
| `challenge/requirements.yml` | Plus de `community.does-not-exist`. Toutes les collections sont **FQCN** (`namespace.collection`). |
| `challenge/requirements.txt` | Plus de `9999.0.0` (versions PyPI réelles). |
| `challenge/bindep.txt` | Présent, system deps déclarés. |

## 🧩 Indices

### Méthode de debug

```bash
# 1. Tenter le build avec les fichiers buggy (échec attendu)
ansible-builder build \
    -f execution-environment-buggy.yml \
    --container-runtime podman --verbosity 3

# 2. Lire les erreurs ansible-builder (souvent claires sur le schéma)
# 3. Tester chaque collection individuellement
ansible-galaxy collection install community.does-not-exist
# → Erreur 404, on confirme la collection n'existe pas

# 4. Vérifier les versions PyPI
pip index versions kubernetes
# → 30.1.0 est la dernière en 2026, pas 9999.0.0
```

### Fichiers corrigés à produire

```bash
mkdir -p challenge/

cat > challenge/execution-environment.yml <<'YAML'
---
version: 3                                # ← ajouté
images:
  base_image:
    name: ghcr.io/ansible-community/community-ee-minimal:latest
dependencies:
  ansible_core:
    package_pip: ansible-core==2.18.0
  galaxy: ../requirements.yml
  python: ../requirements.txt
  system: ../bindep.txt
YAML

cat > challenge/requirements.yml <<'YAML'
---
collections:
  - name: community.docker
    version: 3.10.4
  - name: ansible.posix
    version: 1.5.4
YAML

cat > challenge/requirements.txt <<'TXT'
kubernetes==30.1.0
hvac==2.3.0
TXT

cat > challenge/bindep.txt <<'TXT'
[platform:rpm]
git
podman
TXT
```

## 🚀 Lancement

```bash
cd labs/ee/debug/challenge/
ansible-builder build --container-runtime podman -t lab88-fixed-ee:latest
```

## 🧪 Validation

```bash
pytest -v labs/ee/debug/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ee/debug/ clean
```

## 💡 Pour aller plus loin

- **`ansible-builder build --verbosity 3`** : log complet du build,
  utile pour identifier l'étape qui plante.
- **`podman run --rm <image-partielle> /bin/bash`** : entrer dans une
  image partiellement construite pour debugger.
- **`ansible-navigator collections --eei <ee>`** : lister les collections
  effectivement embarquées (preuve que le build a bien intégré).
- **`hadolint`** sur `Containerfile` généré par builder : détecte
  d'autres anti-patterns OCI.
