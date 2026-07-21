# 🎯 Challenge : comparer 3 Execution Environments, preuves à l'appui

## ✅ Mission

Écrire `inspect.sh` (livré en squelette à la racine du lab), l'exécuter,
et produire un rapport de comparaison factuel.

| Livrable | Attente |
| --- | --- |
| `inspect.sh` | complété (plus de `???`), exécutable, syntaxe bash valide. Inspecte les 3 EE `creator-ee`, `awx-ee`, `community-ee-minimal` avec podman et ansible-navigator |
| `inspect-output/comparison.md` | généré par VOTRE script : un tableau Markdown avec, pour chacun des 3 EE, la version d'ansible-core constatée et la taille d'image |

Le rapport doit venir de l'exécution réelle du script (`./inspect.sh`),
pas d'un copier-coller : les versions constatées changent avec les tags
`latest`, c'est justement l'intérêt de l'inspection.

## 🧩 Indices

- Version d'ansible-core dans une image :
  `podman run --rm <ee> ansible --version | head -1`.
- Taille : `podman image inspect <ee> --format '{{.Size}}'`.
- Collections embarquées : `podman run --rm <ee> ansible-galaxy collection
  list`, ou `ansible-navigator collections --eei <ee> --mode stdout`.
- Générer un tableau Markdown en bash : accumulez des lignes
  `| image | version | taille |` dans le fichier de sortie.

## 🚀 Lancement

```bash
cd labs/ee/inspection/
./inspect.sh
cat inspect-output/comparison.md
```

## 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées. Ce journal
doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/inspection/challenge/tests/
```

Pytest vérifie votre script (syntaxe bash réelle, outils utilisés, 3 EE
couverts) et le contenu factuel du rapport généré. Il ne tire pas les
images lui-même (plusieurs Go) : c'est votre exécution qui produit le
rapport.

## 🧹 Reset

```bash
dsoxlab clean ee-inspection
```

## 💡 Pour aller plus loin

- `skopeo inspect docker://<ee>` : métadonnées sans pull complet.
- Choisir son EE : minimal pour lab et démos, awx-ee pour AWX/AAP,
  creator-ee pour le développement de collections.
