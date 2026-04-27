# 🎯 Challenge — Lint production + pre-commit hooks

## ✅ Objectif

Le test pytest valide la **structure** des fichiers livrés dans ce lab :

- Lab 68 : Lint production + pre-commit hooks.

## 🧩 Indices

C'est un challenge structurel. Posez `solution.sh` minimal :

```bash
echo "Lab 68 : Lint production + pre-commit hooks validé par pytest." > challenge/solution.sh
chmod +x challenge/solution.sh
```

## 🚀 Lancement (optionnel)

```bash
cd labs/tests/ansible-lint-production/
pre-commit install
pre-commit run --all-files
```

## 🧪 Validation

```bash
pytest -v labs/tests/ansible-lint-production/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/tests/ansible-lint-production/ clean
```
