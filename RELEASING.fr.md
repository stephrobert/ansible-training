# Publier une version d'ansible-training

**Langue :** [English](./RELEASING.md) · [Français](./RELEASING.fr.md)

Ce dépôt livre du **contenu de labs**, pas un paquet Python. Une version publie
un **bundle `tar.gz`** du catalogue de labs comme asset d'une Release GitHub :
pas de PyPI, pas de wheel, aucun registre d'artefacts externe.

## Ce que contient une version

Le workflow `release.yml` construit `ansible-training-<version>.tar.gz` avec :

- `labs/`, `meta.yml`, `conftest.py`, `inventory/`, `ansible.cfg`,
  `requirements.yml`, `requirements.txt`
- `solution/`, qui reste **chiffré via ansible-vault** dans l'archive
- les documents de gouvernance (`README`, `LICENSE`, `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, `CHANGELOG`)

Il **exclut** le pilotage local (`.claude/`, `CLAUDE.md`), les fichiers générés
(`.venv/`, `.ansible_facts/`, caches), la **clé SSH privée** (`ssh/id_ed25519`)
et le **mot de passe du vault** (`.vault-pass`). Une empreinte `.sha256` est
publiée à côté de l'archive.

## Produire une version

1. Mettre à jour `CHANGELOG.md` et `CHANGELOG.fr.md` (basculer les entrées sous
   une nouvelle version).
2. S'assurer que `dsoxlab validate-structure` est vert en local.
3. Taguer et pousser le tag, ce qui déclenche `release.yml` :

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. Le workflow construit le `tar.gz`, son `.sha256`, et crée la Release GitHub
   avec des notes générées automatiquement.

## Vérifier une version

```bash
sha256sum -c ansible-training-<version>.tar.gz.sha256
tar tzf ansible-training-<version>.tar.gz | head
```

Contrôle à faire une fois, après le premier bundle : vérifier qu'aucun secret
n'a fui dans l'archive.

```bash
tar tzf ansible-training-<version>.tar.gz | grep -E 'vault-pass|id_ed25519$' \
  && echo "FUITE : ne pas publier" || echo "OK"
```

> Les commits et les tags sont créés par un humain, jamais par un assistant.
