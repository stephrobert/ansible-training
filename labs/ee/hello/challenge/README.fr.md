# 🎯 Challenge — Lancer un premier playbook dans un EE

## ✅ Objectif

À la racine du lab, produire 4 fichiers qui démontrent l'utilisation
d'`ansible-navigator` avec un Execution Environment officiel
(`creator-ee`).

| Fichier | Attente |
| --- | --- |
| `setup-ee.sh` | Exécutable. Vérifie/installe `podman` et `ansible-navigator`. |
| `inventory.yml` | YAML valide. Hôtes `web1.lab` et `db1.lab` dans le groupe `all`, chacun déclarant son `ansible_host` (IP joignable). |
| `ping.yml` | Module FQCN `ansible.builtin.ping`. |
| `ansible-navigator.yml` | Référence l'image `creator-ee` dans `execution-environment.image:`. |

## 🧩 Indices

### Étape 1 — `setup-ee.sh` (script à compléter)

```bash
cat > setup-ee.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
command -v ??? >/dev/null || sudo dnf install -y ???
command -v ??? >/dev/null || pipx install ???
podman pull ???                            # image creator-ee officielle
SH
chmod +x setup-ee.sh
```

### Étape 2 — `inventory.yml`

```yaml
---
all:
  hosts:
    ???:                                   # web1.lab et db1.lab
    ???:
```

### Étape 3 — `ping.yml`

```yaml
---
- name: Hello EE
  hosts: ???
  gather_facts: false
  tasks:
    - name: Pinger
      ansible.builtin.???:
```

### Étape 4 — `ansible-navigator.yml`

```yaml
---
ansible-navigator:
  execution-environment:
    image: ???                  # ghcr.io/ansible/creator-ee:latest
    container-engine: ???       # podman (pas docker — convention RHCE 2026)
    pull:
      policy: ???                # 'missing' (pull si absent), 'always' (CI), 'never'
  mode: ???                      # 'stdout' (CI), 'interactive' (TUI)
  logging:
    level: info
```

> 💡 **Pièges** :
>
> - **`podman` vs `docker`** : Red Hat préconise Podman (rootless, pas de
>   daemon). À l'EX294 2026, c'est `podman` partout. Docker fonctionne
>   mais reste un anti-pattern dans l'éco RHEL.
> - **`pull.policy: missing`** : pull seulement si l'image absente
>   localement. **`always`** force un pull (utile en CI), **`never`**
>   exige que l'image soit déjà présente (utile offline).
> - **`mode: stdout`** indispensable pour CI/scripts. Le défaut
>   `interactive` (TUI) bloque dans un script non-tty.

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
de creator-ee) reste manuel.

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
