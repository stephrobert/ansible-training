# 🎯 Challenge — Valider la structure du scénario Molecule

## ✅ Objectif

Le scénario Molecule **par défaut** est livré dans `molecule/default/`.
Le challenge consiste à **vérifier qu'il est conforme** au standard :

| Fichier | Présence requise |
| --- | --- |
| `molecule/default/molecule.yml` | ✅ |
| `molecule/default/converge.yml` | ✅ |
| `molecule/default/verify.yml` | ✅ |

Et le contenu de `molecule.yml` doit déclarer :

- `driver:` (name = `default`/`delegated`/`docker`/`podman`)
- `platforms:` (≥ 1 plateforme)
- `verifier:` (name = `ansible`/`testinfra`/`goss`)

## 🧩 Indices

Le challenge est **purement structurel** — pas de playbook à écrire. Posez
juste un `solution.sh` minimal qui valide votre lecture des fichiers
Molecule existants.

```bash
cat > labs/molecule/introduction/challenge/solution.sh <<'EOF'
#!/usr/bin/env bash
# Stub — le test pytest valide la structure des fichiers Molecule.
echo "Challenge lab 62 : structure Molecule vérifiée par pytest."
EOF
chmod +x labs/molecule/introduction/challenge/solution.sh
```

## 🚀 Lancement

```bash
# (Optionnel) lancer Molecule pour exécuter le cycle complet
cd labs/molecule/introduction && molecule test
```

🔍 Si Podman/Docker n'est pas disponible, le test pytest reste valide
(il vérifie juste les fichiers, pas leur exécution).

## 🧪 Validation automatisée

```bash
pytest -v labs/molecule/introduction/challenge/tests/
```

Le test vérifie :

- `molecule.yml`, `converge.yml`, `verify.yml` existent dans `molecule/default/`.
- `molecule.yml` déclare `driver`, `platforms` (≥1), `verifier`.
- `converge.yml` appelle le rôle `webserver`.
- `verify.yml` utilise au moins une `ansible.builtin.assert`.

## 🧹 Reset

```bash
make -C labs/molecule/introduction clean
```

## 💡 Pour aller plus loin

- Lab **63** : ajouter `prepare.yml` + `requirements.yml`.
- Lab **64** : cycle TDD complet sur un nouveau rôle.
- Lab **65** : multi-distro (RHEL + Debian + Ubuntu).
