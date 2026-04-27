# 🎯 Challenge — Lancer un premier playbook dans un EE

## ✅ Objectif

À la racine du lab, produire 4 fichiers qui démontrent l'utilisation
d'`ansible-navigator` avec un Execution Environment officiel
(`creator-ee`).

| Fichier | Attente |
| --- | --- |
| `setup-ee.sh` | Exécutable. Vérifie/installe `podman` et `ansible-navigator`. |
| `inventory.yml` | YAML valide. Hôtes `web1.lab` et `db1.lab` dans le groupe `all`. |
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
> - **Test structurel** : le test ne lance pas Podman. Il valide juste
>   que les fichiers existent et contiennent les bons mots-clés. Vous
>   pouvez passer le test sans avoir Podman installé.

## 🚀 Lancement

```bash
cd labs/ee/hello/
./setup-ee.sh
ansible-navigator run ping.yml -i inventory.yml --mode stdout
```

## 🧪 Validation

```bash
pytest -v labs/ee/hello/challenge/tests/
```

Le test est **structurel** : il valide les fichiers ci-dessus sans
exécuter Podman.

## 🧹 Reset

```bash
make -C labs/ee/hello/ clean
```

## 💡 Pour aller plus loin

- `ansible-navigator --mode interactive` : interface TUI navigable au
  clavier (`:run`, `:doc`, `:collections`).
- `--pp always` : force un pull à chaque exécution (utile en CI quand
  on push souvent l'EE).
- `~/.ansible-navigator.yml` : config globale au lieu de par-projet.
