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
(`.venv/`, `.ansible_facts/`, caches), la **clé SSH privée**
(`ssh/id_ed25519`) et le **mot de passe du vault** (`.vault-pass`).

Quatre assets sont attachés à chaque release :

| Asset | À quoi il sert |
| --- | --- |
| `ansible-training-<version>.tar.gz` | le catalogue lui-même |
| `….tar.gz.sha256` | l'intégrité, vérifiable hors ligne |
| `….tar.gz.cosign.bundle` | la signature Cosign keyless |
| `provenance.intoto.jsonl` | la provenance SLSA, l'asset que cherche le contrôle Signed-Releases d'OpenSSF Scorecard |

## Pourquoi trois jobs, et pas un seul

Le workflow est découpé en **construire**, **attester**, **publier**, et ce
découpage est la seule chose qui sépare SLSA Build Level 2 de Level 3.

La documentation GitHub le dit en deux phrases : « Artifact attestations by
itself provides SLSA v1.0 Build Level 2 », et « Reusable workflows can provide
isolation between the build process and the calling workflow, to meet SLSA
v1.0 Build Level 3 ». Tant que le job qui construit l'archive est aussi celui
qui signe sa provenance, rien n'empêche techniquement le processus de build de
produire une provenance qui ment. Le niveau 3 exige que la signature se fasse
hors de sa portée.

D'où `.github/workflows/attester.yml`, appelé comme workflow réutilisable :

- il est le **seul workflow du dépôt** à recevoir `attestations: write` ;
- il reçoit **un nom et une empreinte**, jamais l'archive ni le dépôt : il ne
  fait aucun `checkout` ;
- le job de publication peut écrire la release mais **ne peut pas attester**,
  faute de cette permission ;
- l'archive est recontrôlée contre son empreinte **avant** publication, pour
  qu'un artefact altéré entre deux jobs ne soit pas publié avec une provenance
  qui ne le décrit pas.

Jusqu'au 2026-10-09, ce dépôt attestait depuis son job de build — niveau 2 —
alors que son README affichait le badge niveau 3. Les cinq catalogues voisins
avaient déjà fait le pas ; celui-ci était resté en arrière.

## Vérifier une version

Intégrité et contenu :

```bash
sha256sum -c ansible-training-<version>.tar.gz.sha256
tar tzf ansible-training-<version>.tar.gz | head
```

À faire une fois, après le premier bundle : vérifier qu'aucun secret n'a fui
dans l'archive.

```bash
tar tzf ansible-training-<version>.tar.gz | grep -E 'vault-pass|id_ed25519$' \
  && echo "FUITE : ne pas publier" || echo "OK"
```

Provenance du build. Prouve que l'archive a bien été produite par le workflow de
ce dépôt, et non reconstruite par quelqu'un d'autre :

```bash
gh attestation verify ansible-training-<version>.tar.gz \
  --repo stephrobert/ansible-training
```

**La vérification qui atteste le niveau 3** nomme le workflow signataire. Elle
échoue si la provenance a été produite ailleurs que par le workflow
d'attestation isolé, et c'est elle qu'il faut lancer à la première release pour
confirmer que la chaîne tient :

```bash
gh attestation verify ansible-training-<version>.tar.gz \
  --repo stephrobert/ansible-training \
  --signer-workflow stephrobert/ansible-training/.github/workflows/attester.yml
```

Signature Cosign keyless. Les **deux** options de certificat sont obligatoires :
sans elles, `cosign verify-blob` accepte n'importe quelle identité, ce qui vide
la vérification de son sens.

```bash
cosign verify-blob \
  --bundle ansible-training-<version>.tar.gz.cosign.bundle \
  --certificate-identity-regexp "https://github.com/stephrobert/ansible-training/.github/workflows/release.yml@.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ansible-training-<version>.tar.gz
```

> **Piège de version Cosign.** La CI installe **Cosign 3.x**, qui écrit un
> nouveau format de bundle. Un **Cosign 2.x** local répond `no signatures found`
> sur une archive pourtant parfaitement signée : la release n'est pas cassée,
> c'est l'outil local qui ne sait pas lire le format. Vérifiez `cosign version`
> et alignez-le avant de conclure quoi que ce soit.

> Les commits et les tags sont créés par un humain, jamais par un assistant.
