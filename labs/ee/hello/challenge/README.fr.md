# 🎯 Challenge — Lancer un premier playbook dans un EE

## ✅ Objectif

À la racine du lab, produire 4 fichiers qui démontrent l'utilisation
d'`ansible-navigator` avec un Execution Environment officiel
(`community-ansible-dev-tools`).

| Fichier | Attente |
| --- | --- |
| `setup-ee.sh` | Exécutable. Vérifie/installe `podman` et `ansible-navigator`. |
| `inventory.yml` | YAML valide. Hôtes `web1.lab` et `db1.lab` dans le groupe `all`, chacun déclarant son `ansible_host` (IP joignable). |
| `ping.yml` | Module FQCN `ansible.builtin.ping`. |
| `ansible-navigator.yml` | Référence l'image `community-ansible-dev-tools` dans `execution-environment.image:`. |

## 🧩 Bloqué ?

```bash
dsoxlab hint ee-hello
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
cd labs/ee/hello/
./setup-ee.sh
ansible-navigator run ping.yml -i inventory.yml --mode stdout
```

## 📓 Journal de commandes

Consignez dans `challenge/solution.sh` les commandes exécutées (setup,
run navigator). Ce journal doit exister pour que pytest s'exécute :

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/hello/challenge/tests/
```

Les tests exécutent réellement `bash -n` sur votre script,
`ansible-inventory` sur votre inventaire et `ansible-playbook
--syntax-check` sur votre playbook. Seul le run dans l'EE (Podman + pull
de community-ansible-dev-tools) reste manuel.

## 🧹 Reset

```bash
dsoxlab clean ee-hello
```

## 💡 Pour aller plus loin

- `ansible-navigator --mode interactive` : interface TUI navigable au
  clavier (`:run`, `:doc`, `:collections`).
- `--pp always` : force un pull à chaque exécution (utile en CI quand
  on push souvent l'EE).
- `~/.ansible-navigator.yml` : config globale au lieu de par-projet.
