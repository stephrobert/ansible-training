# 🎯 Challenge — Faire tourner `ansible-pull` depuis db1.lab

## ✅ Objectif

Faire en sorte que **db1.lab se configure lui-même** en mode pull : un
dépôt Git contenant un `pull-playbook.yml`, cloné et exécuté sur db1 par
**`ansible-pull`**. Pas de démo pré-livrée : c'est vous qui créez le dépôt,
le playbook et le script d'orchestration.

Les tests ne lisent pas vos fichiers : ils lancent votre script puis
vérifient **l'état de db1.lab**.

| État attendu sur db1.lab | Preuve |
| --- | --- |
| `/var/lib/ansible-pull/` est un clone Git contenant `pull-playbook.yml` | `ansible-pull` a bien cloné (personne n'a copié le marqueur à la main) |
| `/tmp/lab98-pull-marker.txt` existe, owner `root`, mode `0644` | le playbook tiré s'est exécuté avec privilèges |
| Le marqueur contient `ansible-pull executed` et le hostname de la machine | le play a tourné **sur db1**, pas sur le control node |

## 🧩 Étapes (à vous d'écrire le contenu)

### Étape 1 — Le dépôt Git local

Créer `repo-pull/` dans ce lab, y écrire `pull-playbook.yml`, puis en faire
un vrai dépôt (`git init` + commit). Le playbook cible la machine qui
l'exécute, pas un hôte distant :

```yaml
---
- hosts: ???                   # la cible s'exécute elle-même
  connection: ???
  become: true
  gather_facts: true
  tasks:
    - name: Marker pull executed
      ansible.builtin.copy:
        dest: ???
        content: |
          ansible-pull executed at: {{ ??? }}
          hostname: {{ ??? }}
        owner: ???
        group: ???
        mode: ???
```

### Étape 2 — Le script orchestrateur `challenge/solution.sh`

Un script shell (pas un playbook) qui, dans l'ordre :

1. Installe `ansible-core` et `git` sur db1.lab (le seul push du lab :
   l'amorçage). Astuce : `ansible db1.lab -b -m ansible.builtin.dnf -a ...`
   résout l'IP via l'inventaire, contrairement à un `ssh db1.lab` direct.
2. Transfère `repo-pull/` sur db1 (par exemple sous `/tmp/lab98-repo-pull`).
   Attention : le `.git/` doit survivre au transfert, sinon `ansible-pull`
   ne peut pas cloner. Une archive `tar` est votre amie. En production, ce
   serait une URL `https://` et cette étape n'existerait pas.
3. Lance `ansible-pull` **sur db1** (via `ansible -b -m ansible.builtin.command`)
   avec `-U <chemin-du-repo-sur-db1>`, `-d /var/lib/ansible-pull` et le nom
   du playbook.

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 1. amorçage : outillage sur la cible
ansible db1.lab -b -m ansible.builtin.dnf -a "???"

# 2. transférer le dépôt (préserver .git/)
???

# 3. la cible tire et s'applique sa config
ansible db1.lab -b -m ansible.builtin.command \
  -a "ansible-pull -U ??? -d ??? ???"
```

> 💡 **Pièges** :
>
> - **`hosts: localhost` + `connection: local`** dans `pull-playbook.yml` :
>   c'est la cible elle-même qui exécute. Un `hosts: db1.lab` ne matcherait
>   rien dans l'inventaire par défaut d'`ansible-pull`.
> - **`ansible-pull` clone via git** : le chemin passé à `-U` doit être un
>   dépôt Git valide **vu depuis db1** (dossier local sur db1 ou URL).
> - **Owner `root`** : `ansible-pull` doit tourner avec élévation (`-b` sur
>   la commande ad-hoc), sinon le marqueur appartiendra à `ansible`.

## 🚀 Lancement

```bash
chmod +x labs/pratiques/ansible-pull-gitops/challenge/solution.sh
bash labs/pratiques/ansible-pull-gitops/challenge/solution.sh
```

## 🧪 Validation automatisée

```bash
pytest -v labs/pratiques/ansible-pull-gitops/challenge/tests/
```

Les tests remettent db1 à zéro, exécutent votre `solution.sh`, puis
vérifient sur db1 le clone Git et le marqueur (owner, mode, contenu).

## 🧹 Reset

```bash
dsoxlab clean pratiques-ansible-pull-gitops
```

## 💡 Pour aller plus loin

- **Exécution périodique** : posez un cron ou un timer systemd qui relance
  `ansible-pull` toutes les 30 minutes — le nœud converge tout seul.
- **Cloud-init** : intégrez `ansible-pull` dans `runcmd:` pour un bootstrap
  immuable au premier boot.
- **AAP Tower** : ne supporte PAS le pull. Si vous visez AAP, restez en push.
