# Versionner et publier un rôle Ansible

## Workflow Git semver

```bash
# 1. Tester le rôle (Molecule + ansible-lint)
molecule test
ansible-lint --profile=production roles/webserver/

# 2. Mettre à jour CHANGELOG.md
# 3. Tagger en semver (vMAJOR.MINOR.PATCH)
git add CHANGELOG.md
git commit -m "release: v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0 - Multi-distro support"

# 4. Pousser le tag
git push origin main --tags
```

## Publication sur Ansible Galaxy

### Prérequis

1. Compte sur https://galaxy.ansible.com lié à votre compte GitHub
2. **Token API Galaxy** depuis votre profil
3. `meta/main.yml` complet

### Méthode 1 — Via GitHub Webhook (rôles)

1. Sur Galaxy, **My Content → Add Content → Import Role from GitHub**
2. Sélectionner le repo `stephrobert/ansible-role-webserver`
3. Galaxy importe automatiquement à chaque nouveau tag Git semver

### Méthode 2 — CLI (collections)

```bash
# Build la collection
cd path/to/collection/
ansible-galaxy collection build

# Publier sur Galaxy
ansible-galaxy collection publish \
  stephrobert-networking-1.0.0.tar.gz \
  --api-key=$GALAXY_TOKEN
```

## Pinning dans les `requirements.yml` consommateurs

```yaml
roles:
  - src: stephrobert.webserver
    version: 1.2.0           # ← exact match (production)

  # Ou plage compatible
  - src: stephrobert.webserver
    version: ">=1.2.0,<2.0.0"
```

## Workflow CI/CD complet

Pour automatiser, voir `.github/workflows/release.yml` qui :

1. Lance `molecule test` sur chaque PR
2. Lance `ansible-lint --profile=production`
3. Sur tag `v*.*.*` : publish automatique sur Galaxy via API

## Convention de versionnement

- **Major** (1.0.0 → 2.0.0) : breaking change (variable renommée, structure cassée)
- **Minor** (1.0.0 → 1.1.0) : nouvelle feature rétrocompatible
- **Patch** (1.0.0 → 1.0.1) : bugfix

## Communication

- **CHANGELOG.md** mis à jour à chaque release
- **README.md** mis à jour si nouvelles variables
- **Release notes** GitHub avec exemples de migration si breaking
