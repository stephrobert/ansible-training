# 🎯 Challenge — Faire tourner `ansible-pull` depuis db1.lab

## ✅ Objectif

Créer un mini-repo Git local contenant un `pull-playbook.yml`, puis depuis `db1.lab` lancer **`ansible-pull`** qui clone le repo et exécute le playbook localement. Le playbook dépose un fichier preuve dans `/tmp/`.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible (qui exécute) | `db1.lab` (mode pull = la cible se configure elle-même) |
| Repo Git source | `labs/pratiques/ansible-pull-gitops/repo-pull/` (local) |
| Playbook dans le repo | `pull-playbook.yml` |
| Fichier produit | `/tmp/lab98-pull-marker.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Marqueur `ansible-pull executed` + hostname |

## 🧩 Indices

### Étape 1 — Créer le mini-repo Git local

```bash
cd labs/pratiques/ansible-pull-gitops/
mkdir -p repo-pull
cat > repo-pull/pull-playbook.yml <<'EOF'
---
- hosts: ???                   # ← localhost (mode pull)
  connection: ???              # ← local
  become: ???
  gather_facts: true
  tasks:
    - name: Marker pull executed
      ansible.builtin.copy:
        dest: ???              # ← /tmp/lab98-pull-marker.txt
        content: |
          ansible-pull executed at: {{ ansible_date_time.iso8601 }}
          hostname: {{ ansible_hostname }}
        owner: ???
        group: ???
        mode: ???
EOF

cd repo-pull
git init
git -c user.email=a@b -c user.name=lab add .
git -c user.email=a@b -c user.name=lab commit -m "initial pull-playbook"
```

### Étape 2 — Script orchestrateur `solution.sh`

Créer **`challenge/solution.sh`** (script shell, pas un playbook) :

```bash
#!/bin/bash
# solution.sh — installe ansible-pull sur db1.lab et exécute le pull
set -e

REPO_PATH="???"                # ← chemin absolu vers repo-pull/

ssh -o StrictHostKeyChecking=no -i ssh/id_ed25519 ansible@db1.lab "
  sudo dnf install -y ansible-core git
  sudo ansible-pull -U $REPO_PATH -d /var/lib/ansible-pull pull-playbook.yml
"
```

Rendre exécutable :

```bash
chmod +x challenge/solution.sh
```

> 💡 **Pièges** :
> - `ansible-pull` nécessite **`ansible-core` + `git`** installés sur la cible.
> - Le path **`-U`** doit être accessible **depuis db1.lab**. Avec un repo local, monter le dossier ou utiliser `https://`.
> - **`hosts: localhost` + `connection: local`** dans le playbook (pas `db1.lab`) car c'est la **cible elle-même** qui s'exécute.

### Étape 3 — Lancement

```bash
bash labs/pratiques/ansible-pull-gitops/challenge/solution.sh
```

## 🚀 Lancement

```bash
bash labs/pratiques/ansible-pull-gitops/challenge/solution.sh
```

## 🧪 Validation automatisée

```bash
LAB_NO_REPLAY=1 pytest -v labs/pratiques/ansible-pull-gitops/challenge/tests/
```

Tests structurels uniquement (le repo doit exister, le script doit invoquer `ansible-pull`, le fichier preuve doit être déposé).

## 🧹 Reset

```bash
make -C labs/pratiques/ansible-pull-gitops/ clean
```

## 💡 Pour aller plus loin

- **Mode push équivalent** : `ansible-playbook` depuis le control node = pattern classique RHCE.
- **`cron`/systemd timer** : exécution périodique de `ansible-pull` sur les nœuds Edge.
- **Cloud-init** : intégrer `ansible-pull` dans `runcmd:` pour bootstrap immuable au boot.
- **AAP Tower** : NE supporte PAS le pull. Si vous visez AAP, restez en push.
