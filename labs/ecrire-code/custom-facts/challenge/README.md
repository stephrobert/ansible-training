# 🎯 Challenge — Combiner custom facts INI + script Bash

## ✅ Objectif

Déposer **deux** custom facts sur `db1.lab` (un INI statique + un script Bash dynamique), puis dans un playbook **lire les deux** et écrire un fichier preuve qui combine les valeurs.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Custom fact 1 | `/etc/ansible/facts.d/lab14a.fact` (INI, mode `0644`) |
| Custom fact 2 | `/etc/ansible/facts.d/lab14a-uptime.fact` (script Bash, mode `0755`) |
| Fichier produit | `/tmp/lab14a-custom-facts.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Valeurs des 2 facts (au moins 4 lignes) |

## 🧩 Indices

### Squelette `solution.yml`

```yaml
---
- name: Challenge 14a — custom facts INI + script Bash
  hosts: ???
  become: ???
  gather_facts: false           # ← on collectera explicitement après dépôt

  tasks:
    - name: Créer /etc/ansible/facts.d/
      ansible.builtin.file:
        path: ???
        state: ???
        mode: ???

    - name: Déposer le custom fact INI
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/lab14a.fact
        mode: ???                # ← STATIQUE, non exécutable
        content: |
          [project]
          name = lab14a
          version = ???
          [team]
          owner = ???

    - name: Déposer le custom fact dynamique
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/lab14a-uptime.fact
        mode: ???                # ← EXÉCUTABLE
        content: |
          #!/bin/bash
          cat <<EOF
          {
            "uptime_seconds": $(awk '{print int($1)}' /proc/uptime),
            "kernel": "$(uname -r)"
          }
          EOF

    - name: Re-collecter les facts pour récupérer ansible_local
      ansible.builtin.setup:
        filter: ???                # ← isolat des custom facts

    - name: Déposer le fichier preuve
      ansible.builtin.copy:
        dest: /tmp/lab14a-custom-facts.txt
        content: |
          project: {{ ansible_local.lab14a.project.name }}
          version: {{ ansible_local.lab14a.project.version }}
          owner: {{ ???.???.team.owner }}
          kernel: {{ ???.???.kernel }}
        mode: ???
```

> 💡 **Pièges** :
> - Le **bit exécutable** (`mode: "0755"`) du script dynamique est **critique** : sans, Ansible le lit comme statique et plante car ce n'est pas du JSON/INI valide.
> - Le **2e fact** s'appelle `lab14a-uptime.fact` → accessible via `ansible_local.lab14a-uptime` (le `-` reste dans la clé).
> - **Re-collecter les facts** après dépôt : `ansible.builtin.setup` est nécessaire car `gather_facts: false` initialement.

## 🚀 Lancement

```bash
ansible-playbook labs/ecrire-code/custom-facts/challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/ecrire-code/custom-facts/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/ecrire-code/custom-facts/ clean
```

## 💡 Pour aller plus loin

- **Custom path** : `setup -a "fact_path=/custom/path"` pour ne pas utiliser le défaut `/etc/ansible/facts.d/`.
- **`ansible-lint --profile production`** doit retourner vert.
