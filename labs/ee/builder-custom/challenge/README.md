# 🎯 Challenge — Builder un EE custom avec `ansible-builder`

## ✅ Objectif

Produire les 5 fichiers requis pour builder un EE custom **schéma v3** :

| Fichier | Attente |
| --- | --- |
| `execution-environment.yml` | `version: 3`. `images.base_image.name` contient `community-ee-minimal`. `dependencies.ansible_core.package_pip` pinné avec `==`. |
| `requirements.yml` | Toutes les collections déclarent `version:` (pas de plage `>=` flottante). |
| `requirements.txt` | Toutes les dépendances Python pinnées avec `==`. |
| `bindep.txt` | Contient `[platform:rpm]` (system deps RHEL). |
| `build-ee.sh` | Exécutable. Utilise `--container-runtime podman`. |

## 🧩 Indices

### `execution-environment.yml` (schéma v3)

```yaml
---
version: 3

images:
  base_image:
    name: ???                 # ghcr.io/ansible-community/community-ee-minimal:latest

dependencies:
  ansible_core:
    package_pip: ???          # ansible-core==2.18.0  (pin strict, pas >=)
  ansible_runner:
    package_pip: ansible-runner==2.4.0
  galaxy: requirements.yml
  python: requirements.txt
  system: bindep.txt
```

### `requirements.yml` (collections pinnées)

```yaml
---
collections:
  - name: community.docker
    version: ???              # ex: 3.10.4
  - name: ansible.posix
    version: ???              # ex: 1.5.4
```

### `requirements.txt` (Python pinné)

```text
kubernetes==30.1.0
hvac==2.3.0
```

### `bindep.txt` (system deps)

```text
[platform:rpm]
git
podman
```

### `build-ee.sh`

```bash
cat > build-ee.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ansible-builder build \
    --container-runtime ???                  # podman (pas docker)
    --tag ???                                 # localhost/lab86-custom-ee:latest
    --verbosity 2
SH
chmod +x build-ee.sh
```

> 💡 **Pièges** :
>
> - **Schéma v3 obligatoire** : oublier `version: 3` fait tomber
>   `ansible-builder` sur une erreur cryptique. Le test pytest le
>   vérifie explicitement.
> - **Pinning `==` strict** : `ansible_core: { package_pip: ansible-core==2.18.0 }`.
>   Une plage `>=2.18.0` peut briser la reproductibilité du build (la
>   version installée dépend de la date du build).
> - **Collections** : chaque entrée doit avoir `version:` (pas de
>   `latest`). Le test pytest scanne `requirements.yml` et rejette si
>   absent.
> - **`bindep.txt`** : header `[platform:rpm]` indispensable pour les
>   builds RHEL/AlmaLinux. Pour Debian, ajouter `[platform:dpkg]`.
> - **`localhost/`** dans le tag : convention pour les images locales
>   non-pushed. Sans ce préfixe, Podman peut tenter de chercher l'image
>   sur Docker Hub.

## 🚀 Lancement

```bash
cd labs/ee/builder-custom/
./build-ee.sh
podman run --rm localhost/lab86-custom-ee:latest ansible --version
```

## 🧪 Validation

```bash
pytest -v labs/ee/builder-custom/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ee/builder-custom/ clean
```

## 💡 Pour aller plus loin

- **`additional_build_steps`** dans `execution-environment.yml` :
  injecter des commandes `RUN` arbitraires (custom CA cert, debug tools).
- **Multi-stage build** : `builder_image` séparée pour réduire la
  taille de l'image finale.
- **Signer l'image** : `cosign sign localhost/lab86-custom-ee:latest`
  après build (cf. lab 87 CI).
