# 🎯 Challenge — Combiner custom facts INI + script Bash

## ✅ Objectif

Déposer **deux** custom facts sur `db1.lab` (un INI statique + un script Bash dynamique), puis dans un playbook **lire les deux** et écrire un fichier preuve qui combine les valeurs.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Custom fact 1 | `/etc/ansible/facts.d/lab14a.fact` (INI, mode `0644`) |
| Custom fact 2 | `/etc/ansible/facts.d/lab14a-uptime.fact` (script Bash, mode `0755`) |
| Fichier produit | `/tmp/lab14a-custom-facts.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Valeurs des 2 facts (au moins 4 lignes) |

## 🧩 Bloqué ?

```bash
dsoxlab hint ecrire-code-custom-facts
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/custom-facts/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/custom-facts/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-custom-facts
```

## 💡 Pour aller plus loin

- **Custom path** : `setup -a "fact_path=/custom/path"` pour ne pas utiliser le défaut `/etc/ansible/facts.d/`.
- **`ansible-lint --profile production`** doit retourner vert.
