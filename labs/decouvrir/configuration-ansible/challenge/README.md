# 🎯 Challenge — `ansible.cfg` projet avec `profile_tasks` actif

## ✅ Objectif

Créer un `ansible.cfg` au niveau du lab qui active **`profile_tasks`** + force **`forks=20`** + utilise **`stdout_callback = yaml`**, puis lancer un playbook qui dépose **la sortie de `ansible-config dump --only-changed`** dans un fichier sur `db1.lab`.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab03a-config.txt` |
| Permissions | `0644`, owner `root` |
| Contenu | Sortie de `ansible-config dump --only-changed` (≥3 lignes non vides) |
| `ansible.cfg` doit contenir | `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks` |

## 🧩 Indices

### Étape 1 — `ansible.cfg`

Créer `labs/decouvrir/configuration-ansible/ansible.cfg` avec a minima :

```ini
[defaults]
forks = ???
stdout_callback = ???
callbacks_enabled = ???
host_key_checking = False
```

### Étape 2 — Squelette `solution.yml`

```yaml
---
- name: Challenge 03a — config Ansible
  hosts: ???
  become: ???
  gather_facts: false

  tasks:
    - name: Capturer la config active
      ansible.builtin.command: ansible-config dump --only-changed
      register: ???
      changed_when: ???                # ← lecture seule
      delegate_to: localhost
      become: false

    - name: Déposer la sortie sur db1.lab
      ansible.builtin.copy:
        dest: ???
        content: "{{ ???.stdout }}\n"
        owner: ???
        group: ???
        mode: ???
```

> 💡 **Pièges** :
> - **`delegate_to: localhost`** + **`become: false`** sur la première task car `ansible-config` tourne sur le **control node** (le poste de l'apprenant), pas sur la cible.
> - **`changed_when: false`** sur la commande de lecture pour préserver l'idempotence.
> - **Lancer depuis le dossier du lab** (`cd labs/03a-...`) pour qu'`ansible.cfg` soit pris en compte automatiquement.

## 🚀 Lancement

```bash
cd labs/decouvrir/configuration-ansible/
ansible-playbook challenge/solution.yml
```

## 🧪 Validation automatisée

```bash
pytest -v labs/decouvrir/configuration-ansible/challenge/tests/
```

Le test pytest valide :

- `/tmp/lab03a-config.txt` existe sur `db1.lab` avec mode `0644`, owner `root`.
- ≥3 lignes non vides dans le contenu.
- L'`ansible.cfg` du lab contient bien `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks`.

## 🧹 Reset

```bash
make -C labs/decouvrir/configuration-ansible/ clean
```

## 💡 Pour aller plus loin

- **`ansible-config init --disabled > ansible.cfg`** : génère un fichier de config exhaustif documenté.
- **Variables d'env** : `ANSIBLE_FORKS=50` surcharge sans toucher au fichier.
- **`ansible-lint`** ne vérifie pas le contenu d'`ansible.cfg`. Pour valider la syntaxe : `ansible-config view`.
