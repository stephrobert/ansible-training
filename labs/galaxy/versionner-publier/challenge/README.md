# 🎯 Challenge — CHANGELOG SemVer + procédure de publication

## ✅ Objectif

Vérifier que les **2 documents** livrés sont conformes :

| Fichier | Attentes |
| --- | --- |
| `CHANGELOG.md` | ≥ 2 versions SemVer `[X.Y.Z]`, sections `### Added` + (`Changed` ou `Fixed`) |
| `PUBLISH.md` | mentions `ansible-galaxy`, `Galaxy`, `git tag` (avec exemple `v1.2.0`), `version:` (avec `1.2.0`) |

## 🧩 Indices

`CHANGELOG.md` et `PUBLISH.md` sont livrés. Vérifiez-les puis posez :

```bash
echo "Lab 76 : CHANGELOG + PUBLISH validés par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement

Pas de playbook — c'est un challenge **documentaire**. Pour pratiquer un
release réel sur un fork local :

```bash
cd /tmp && git clone https://github.com/<vous>/ansible-role-webserver
cd ansible-role-webserver
# Éditer CHANGELOG.md, ajouter section [1.3.0]
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin main --tags
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/versionner-publier/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/galaxy/versionner-publier/ clean
```

## 💡 Pour aller plus loin

- **`towncrier`** : génération auto du CHANGELOG depuis fragments PR.
- **GitHub Actions release** : workflow `on: push: tags: ['v*']` qui
  publie sur Galaxy.
- **Galaxy NG** (Automation Hub) : Galaxy privé Red Hat pour entreprise.
