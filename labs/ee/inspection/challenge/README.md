# 🎯 Challenge — Comparer 3 Execution Environments

## ✅ Objectif

Produire un script `inspect.sh` qui inspecte et compare **3 EE
officiels** : `creator-ee`, `awx-ee`, et `community-ee-minimal`.

| Fichier | Attente |
| --- | --- |
| `inspect.sh` | Exécutable. Référence les **3 images** : `creator-ee`, `awx-ee`, `community-ee-minimal`. Utilise `ansible-navigator`. Documente la commande `ansible-galaxy collection list`. |

## 🧩 Indices

```bash
cat > inspect.sh <<'SH'
#!/usr/bin/env bash
# Compare 3 EE officiels — collections embarquées, version Python,
# packages système, taille image.
set -euo pipefail

EES=(
    "ghcr.io/ansible/creator-ee:latest"
    "quay.io/ansible/awx-ee:latest"
    "ghcr.io/ansible-community/community-ee-minimal:latest"
)

for ee in "${EES[@]}"; do
    echo "==============================================="
    echo "  $ee"
    echo "==============================================="

    # Lister les collections embarquées
    ansible-navigator collections \
        --eei "$ee" --pp missing --mode stdout

    # Lister les binaires système (si shell ouvert dans l'image)
    podman run --rm "$ee" rpm -qa | head -20

    # Taille de l'image
    podman image inspect "$ee" --format "{{ "{{" }}.Size{{ "}}" }}" | numfmt --to=iec
done

# Documentation : pour explorer les collections en local
# ansible-galaxy collection list
SH
chmod +x inspect.sh
```

## 🚀 Lancement

```bash
cd labs/ee/inspection/
./inspect.sh | tee inspect-output/comparison.txt
```

## 🧪 Validation

```bash
pytest -v labs/ee/inspection/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ee/inspection/ clean
```

## 💡 Pour aller plus loin

- **Tableau comparatif** : produire un Markdown qui aligne taille,
  collections, Python version pour chaque EE.
- **`skopeo inspect`** : alternative pour inspecter sans pull complet.
- **Choisir son EE** : `community-ee-minimal` pour démos / lab,
  `awx-ee` pour AWX / AAP, `creator-ee` pour le dev local de
  collections.
