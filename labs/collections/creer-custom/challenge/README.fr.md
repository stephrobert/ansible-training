# 🎯 Challenge — Initialiser et builder votre collection minimaliste

## ✅ Objectif

Initialiser une collection **`student.lab95`**, y ajouter **un module Python** qui retourne `"Hello, lab95!"`, builder le tarball, et prouver que la structure passe `ansible-test sanity --docker default --test ansible-doc`.

| Élément | Valeur attendue |
| --- | --- |
| Namespace | `student` |
| Nom collection | `lab95` |
| Version | `1.0.0` |
| Module custom | `plugins/modules/lab95_hello.py` qui retourne `msg="Hello, lab95!"` |
| Tarball | `build/student-lab95-1.0.0.tar.gz` |
| Tags `galaxy.yml` | au moins `[demo, lab95]` |

## 🧩 Bloqué ?

```bash
dsoxlab hint collections-creer-custom
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
cd labs/collections/creer-custom/challenge/
# Suivez les étapes ci-dessus pour produire build/student-lab95-1.0.0.tar.gz
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/creer-custom/challenge/tests/
```

Le test pytest valide la **structure générée** : tarball présent, galaxy.yml conforme, module Python avec `DOCUMENTATION` + `EXAMPLES` + `RETURN`.

## 🧹 Reset

```bash
dsoxlab clean collections-creer-custom
```

## 💡 Pour aller plus loin

- **`ansible-test sanity --docker default --test ansible-doc`** dans la collection.
- **`ansible-galaxy collection publish ...`** vers Galaxy (token API requis).
- **`changelogs/fragments/`** : un YAML par PR plutôt qu'un CHANGELOG.rst monolithique.
