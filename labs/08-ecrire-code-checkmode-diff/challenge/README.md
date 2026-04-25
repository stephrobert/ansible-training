# 🎯 Challenge — `--check --diff` puis exécution réelle

## ✅ Objectif

Écrire `solution.yml` qui pose un fichier `/etc/lab-checkmode.txt` sur **db1.lab**
contenant `Lab checkmode validé`.

Puis exécuter en deux étapes :

1. **Audit** d'abord en `--check --diff` (pour valider le diff) :

   ```bash
   ansible-playbook labs/08-ecrire-code-checkmode-diff/challenge/solution.yml --check --diff
   ```

   Le diff doit afficher l'ajout du fichier (avant: absent, après: contenu).
   Mais le fichier **n'existe pas encore** côté db1.

2. **Exécution réelle** (sans `--check`) :

   ```bash
   ansible-playbook labs/08-ecrire-code-checkmode-diff/challenge/solution.yml --diff
   ```

   Le fichier est créé.

## 🧪 Validation

Le test pytest vérifie sur db1 :

- Le fichier `/etc/lab-checkmode.txt` existe
- Son contenu est `Lab checkmode validé`

```bash
pytest -v labs/08-ecrire-code-checkmode-diff/challenge/tests/
```

## 🚀 Pour aller plus loin

- Avant l'exécution réelle, supprimez manuellement le fichier
  (`ssh ansible@db1.lab sudo rm /etc/lab-checkmode.txt`) et relancez avec
  `--check`. Le diff doit afficher l'ajout.
- Ajoutez une tâche `command:` qui doit s'exécuter même en `--check` (par
  exemple lire la version d'un binaire) en posant `check_mode: false`.
